#!/usr/bin/env bash
# waba_probe.sh — v2 — Session 132
# Probe the MyOperator WABA public API and print a SCREENSHOT-SAFE result.
#
# v2 changes: recognises MYOP_AUTH_TOKEN (the real name, confirmed from the
#             live .env) and reads MYOP_COMPANY_ID from .env instead of
#             hard-coding it, so it can never drift out of date.
#
# What it does:
#   1. Reads the WhatsApp "Authentication" bearer token from /root/wa/.env
#      into a shell variable. Never echoes it.
#   2. Calls the plain templates-LIST endpoint (a GET with no payload).
#   3. Prints ONLY the RESPONSE headers + HTTP status + body.
#      Request headers (which carry the token) are never printed.
#   4. GUARD: scans all output for the token. If any fragment is present,
#      the output is destroyed and the script aborts.
#
# Safe to run repeatedly. Reads nothing, writes nothing, changes nothing.

set -u

ENVFILE="/root/wa/.env"
BASE="https://publicapi.myoperator.co"

HDRS="$(mktemp)"; BODY="$(mktemp)"
cleanup() { rm -f "$HDRS" "$BODY"; }
trap cleanup EXIT

# read one value out of .env without echoing it
read_env() {
  grep -m1 -E "^[[:space:]]*$1[[:space:]]*=" "$ENVFILE" \
    | sed -E "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//" \
    | sed -E 's/^"//; s/"$//; s/^'\''//; s/'\''$//' \
    | tr -d '\r'
}

echo "==================================================================="
echo " WABA AUTHORIZER PROBE  (v2)"
echo " Host : $BASE"
echo " Path : /chat/templates   (GET, no payload)"
echo " When : $(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M:%S %Z')"
echo "==================================================================="
echo

# --- locate the .env -------------------------------------------------
if [ ! -r "$ENVFILE" ]; then
  echo "ABORT: cannot read $ENVFILE"
  exit 2
fi

# --- find the token variable, by NAME only ---------------------------
TOKVAR=""
for cand in MYOP_AUTH_TOKEN WABA_TOKEN WA_TOKEN WHATSAPP_TOKEN \
            MYOP_WABA_TOKEN WABA_AUTH_TOKEN WA_AUTH_TOKEN; do
  if grep -qE "^[[:space:]]*${cand}[[:space:]]*=" "$ENVFILE"; then
    TOKVAR="$cand"
    break
  fi
done

if [ -z "$TOKVAR" ]; then
  echo "ABORT: no known token variable found in $ENVFILE"
  echo "Variable NAMES present in that file (values not shown):"
  grep -oE '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=' "$ENVFILE" \
    | tr -d ' =' | sed 's/^/  - /'
  exit 3
fi

# --- company id, from the file, never hard-coded ---------------------
COMPANY_ID="$(read_env MYOP_COMPANY_ID)"
if [ -z "$COMPANY_ID" ]; then
  echo "ABORT: MYOP_COMPANY_ID is absent or empty in ${ENVFILE}."
  echo "(An empty value and an absent value behave identically — D170.)"
  exit 6
fi

echo "Token source : ${ENVFILE} -> \$${TOKVAR}   (value never displayed)"
echo "Company ID   : ${COMPANY_ID}   (an account id, not a credential)"
echo

# --- read the token value, without echoing it ------------------------
TOKEN="$(read_env "$TOKVAR")"

if [ -z "$TOKEN" ]; then
  echo "ABORT: \$${TOKVAR} exists in ${ENVFILE} but is EMPTY."
  echo "(An empty value and an absent value behave identically — D170.)"
  exit 4
fi
echo "Token length : ${#TOKEN} characters   (a length is not a secret)"
echo

# --- the call. -D writes RESPONSE headers only. No -v. ---------------
CODE="$(curl -sS \
        --connect-timeout 15 --max-time 45 \
        -o "$BODY" -D "$HDRS" \
        -w '%{http_code}' \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "X-MYOP-COMPANY-ID: ${COMPANY_ID}" \
        "${BASE}/chat/templates" 2>/dev/null)" || CODE="000"

# --- GUARD: the token must appear nowhere in what we are about to show
LEAK=0
if grep -qF -- "$TOKEN" "$HDRS" 2>/dev/null; then LEAK=1; fi
if grep -qF -- "$TOKEN" "$BODY" 2>/dev/null; then LEAK=1; fi

if [ "$LEAK" -eq 1 ]; then
  : > "$HDRS"; : > "$BODY"
  unset TOKEN
  echo "ABORT: the token appeared in the server's response."
  echo "Output destroyed. Nothing printed. Do NOT screenshot anything."
  exit 5
fi

unset TOKEN

# --- print the evidence ----------------------------------------------
echo "-------------------------------------------------------------------"
echo " HTTP STATUS : ${CODE}"
echo "-------------------------------------------------------------------"
echo
echo "RESPONSE HEADERS (request headers are never printed):"
echo
sed -e 's/\r$//' "$HDRS" | sed 's/^/  /'
echo
echo "RESPONSE BODY (first 400 bytes):"
echo
head -c 400 "$BODY" | sed 's/^/  /'
echo
echo

# --- the verdict, in one line ----------------------------------------
echo "==================================================================="
case "$CODE" in
  200)
    echo " RESULT: 200 OK — the WABA API is WORKING right now."
    echo "         The outage has ended. The ticket must be corrected."
    ;;
  500)
    ETYPE="$(grep -i '^x-amzn-ErrorType:' "$HDRS" | sed 's/\r$//' | cut -d' ' -f2-)"
    echo " RESULT: 500 — STILL BROKEN."
    if [ -n "$ETYPE" ]; then
      echo "         x-amzn-ErrorType: ${ETYPE}"
    fi
    RID="$(grep -i '^x-amzn-RequestId:' "$HDRS" | sed 's/\r$//' | cut -d' ' -f2-)"
    if [ -n "$RID" ]; then
      echo "         FRESH AWS request id (send this to MyOperator):"
      echo "         ${RID}"
    fi
    ;;
  401|403)
    echo " RESULT: ${CODE} — the gateway REACHED the authorizer and rejected"
    echo "         our token. That is a DIFFERENT fault from the 500."
    echo "         This would be a credential problem on our side."
    ;;
  000)
    echo " RESULT: no response (network, DNS, or timeout). Not the authorizer."
    ;;
  *)
    echo " RESULT: HTTP ${CODE} — unexpected. Show this output to Claude."
    ;;
esac
echo "==================================================================="
echo
echo "This whole screen is safe to photograph and send to MyOperator."
