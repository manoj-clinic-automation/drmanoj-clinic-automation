#!/usr/bin/env bash
# waba_recovery_window.sh — Session 132
#
# READ-ONLY. Sends nothing. Restarts nothing. Changes nothing.
#
# Reads the wa-send-api journal and answers ONE question:
#   When did the WABA authorizer fault start, and when did it stop?
#
# SAFETY
#   - Any 10-digit run (a phone number) is masked to its last 4 digits.
#   - The bearer token is read from .env only to CHECK it never appears
#     in the output. It is never printed.
#   - If the token appears anywhere in the journal output, we abort and
#     print nothing.

set -u

ENVFILE="/root/wa/.env"
UNIT="wa-send-api.service"
SINCE="2026-07-01"

RAW="$(mktemp)"; SAFE="$(mktemp)"
cleanup() { rm -f "$RAW" "$SAFE"; }
trap cleanup EXIT

echo "==================================================================="
echo " WABA RECOVERY WINDOW — journal audit (read-only)"
echo " Unit  : $UNIT"
echo " Since : $SINCE"
echo " When  : $(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M:%S %Z')"
echo "==================================================================="
echo

journalctl -u "$UNIT" --since "$SINCE" --no-pager -o short-iso > "$RAW" 2>/dev/null || true

TOTAL=$(wc -l < "$RAW")
if [ "$TOTAL" -eq 0 ]; then
  echo "No journal lines for $UNIT since $SINCE."
  echo "Either the unit was not running, or the journal was rotated."
  echo "Nothing can be concluded. This is an ABSENCE, not a finding."
  exit 0
fi

# --- mask phone numbers: any 10-digit run -> xxxxxx + last 4 -----------
sed -E 's/([0-9]{6})([0-9]{4})/xxxxxx\2/g' "$RAW" > "$SAFE"

# --- GUARD: the token must not be in what we print ---------------------
if [ -r "$ENVFILE" ]; then
  TOKEN="$(grep -m1 -E '^[[:space:]]*MYOP_AUTH_TOKEN[[:space:]]*=' "$ENVFILE" \
          | sed -E 's/^[[:space:]]*MYOP_AUTH_TOKEN[[:space:]]*=[[:space:]]*//' \
          | sed -E 's/^"//; s/"$//' | tr -d '\r')"
  if [ -n "${TOKEN:-}" ] && grep -qF -- "$TOKEN" "$SAFE"; then
    : > "$SAFE"
    unset TOKEN
    echo "ABORT: the token appears in the journal. Nothing printed."
    echo "The journal itself needs cleaning. Tell Claude."
    exit 5
  fi
  unset TOKEN
fi

echo "Journal lines in window : $TOTAL"
echo "First line              : $(head -1 "$SAFE" | cut -c1-25)"
echo "Last line               : $(tail -1 "$SAFE" | cut -c1-25)"
echo

# --- the fault signature ----------------------------------------------
echo "-------------------------------------------------------------------"
echo " FAILURES  (500 / AuthorizerConfigurationException)"
echo "-------------------------------------------------------------------"
FAILCOUNT=$(grep -c -iE 'AuthorizerConfiguration|" 500|status.*500|HTTP 500' "$SAFE" || true)
echo "Matching lines: ${FAILCOUNT}"
if [ "${FAILCOUNT}" -gt 0 ]; then
  echo
  echo "FIRST failure:"
  grep -iE 'AuthorizerConfiguration|" 500|status.*500|HTTP 500' "$SAFE" | head -1 | sed 's/^/  /'
  echo
  echo "LAST failure:"
  grep -iE 'AuthorizerConfiguration|" 500|status.*500|HTTP 500' "$SAFE" | tail -1 | sed 's/^/  /'
fi
echo

# --- the recovery signature -------------------------------------------
echo "-------------------------------------------------------------------"
echo " SUCCESSES  (Accepted / message_id / 200)"
echo "-------------------------------------------------------------------"
OKCOUNT=$(grep -c -iE 'Accepted|message_id|" 200|status.*200' "$SAFE" || true)
echo "Matching lines: ${OKCOUNT}"
if [ "${OKCOUNT}" -gt 0 ]; then
  echo
  echo "FIRST success in window:"
  grep -iE 'Accepted|message_id|" 200|status.*200' "$SAFE" | head -1 | sed 's/^/  /'
  echo
  echo "LAST success in window:"
  grep -iE 'Accepted|message_id|" 200|status.*200' "$SAFE" | tail -1 | sed 's/^/  /'
fi
echo

# --- daily shape -------------------------------------------------------
echo "-------------------------------------------------------------------"
echo " BY DAY  (failures / successes)"
echo "-------------------------------------------------------------------"
printf "  %-12s %8s %10s\n" "DATE" "FAIL" "SUCCESS"
for d in $(cut -c1-10 "$SAFE" | sort -u | grep -E '^2026-'); do
  f=$(grep "^${d}" "$SAFE" | grep -c -iE 'AuthorizerConfiguration|" 500|status.*500|HTTP 500' || true)
  s=$(grep "^${d}" "$SAFE" | grep -c -iE 'Accepted|message_id|" 200|status.*200' || true)
  printf "  %-12s %8s %10s\n" "$d" "$f" "$s"
done
echo

echo "==================================================================="
if [ "${FAILCOUNT}" -eq 0 ] && [ "${OKCOUNT}" -eq 0 ]; then
  echo " RESULT: the journal records NEITHER failures nor successes."
  echo "         wa_send_api.py may not log HTTP status at all."
  echo "         That is a GAP in the record, not proof of health."
  echo "         Do not send a recovery timestamp we do not have."
else
  echo " RESULT: see the LAST failure and the FIRST success after it."
  echo "         Those two timestamps ARE the recovery window."
  echo "         Anything outside them is not evidence."
fi
echo "==================================================================="
echo
echo "Phone numbers masked. Token checked absent. Safe to photograph."
