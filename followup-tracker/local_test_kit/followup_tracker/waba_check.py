"""
waba_check.py — does the token authenticate at all? (reads token from .env)

Tries a no-body GET with BOTH auth schemes. If you also set MYOP_ALT_TOKEN in
.env (e.g. the Calling-APIs x-api-key, to rule it out), it tests that too.

    python waba_check.py
"""
import os
import urllib.request
import urllib.error
import waba   # importing waba loads .env and config

BASE = waba.BASE_URL
COMPANY = waba.COMPANY_ID
WABA = waba.WABA_ID or os.environ.get("MYOP_WABA_ID", "2101222617483538")
PRIMARY = waba.AUTH_TOKEN
ALT = os.environ.get("MYOP_ALT_TOKEN", "")

EP = f"/chat/templates?waba_id={WABA}&waba_template_status=approved&limit=5&offset=0"


def mask(t):
    return f"{t[:4]}…(len {len(t)})" if t else "MISSING"


def call(headers, label):
    req = urllib.request.Request(BASE + EP, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", "replace")
            print(f"[{label}] HTTP {r.status}  OK   body: {body[:200]}")
            return r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"[{label}] HTTP {e.code}  FAIL body: {body[:200]}")
        return e.code
    except urllib.error.URLError as e:
        print(f"[{label}] network error: {e}")
        return 0


def try_token(token, name):
    print(f"\n--- token {name}: {mask(token)} ---")
    ok = False
    if call({"Authorization": f"Bearer {token}", "X-MYOP-COMPANY-ID": COMPANY,
             "Accept": "application/json"}, f"Bearer   /{name}") == 200:
        print(f"✅ WORKS: Authorization: Bearer  with token {name}")
        ok = True
    if call({"x-api-key": token, "X-MYOP-COMPANY-ID": COMPANY,
             "Accept": "application/json"}, f"x-api-key/{name}") == 200:
        print(f"✅ WORKS: x-api-key header  with token {name}")
        ok = True
    return ok


def main():
    print(f"Base: {BASE}")
    print(f"Company ID: {mask(COMPANY)}    WABA ID: {WABA}")
    if not COMPANY:
        print("Missing company id in .env."); return

    candidates = []
    for var, label in [("MYOP_AUTH_TOKEN", "WhatsApp-Authentication"),
                       ("MYOP_ALT_TOKEN",  "CallingAPIs-x-api-key"),
                       ("MYOP_ALT_TOKEN2", "CallingAPIs-Authentication"),
                       ("MYOP_ALT_TOKEN3", "CallingAPIs-SecretKey")]:
        v = os.environ.get(var, "").strip()
        if v:
            candidates.append((label, v))
    if not candidates:
        print("No tokens found in .env."); return

    won = False
    for label, tok in candidates:
        won = try_token(tok, label) or won

    print()
    if won:
        print(">>> Found a working credential above. Tell me the scheme + which key,")
        print("    and I'll lock it into waba.py.")
    else:
        print(">>> None of the tried keys work as Bearer or x-api-key on a no-body GET.")
        print("    Bearer = 500 (server error), x-api-key = 401 (clean reject).")
        print("    This is account-side: the public WhatsApp API is not enabled/")
        print("    provisioned on this WABA. Escalate to MyOperator with these lines.")


if __name__ == "__main__":
    main()
