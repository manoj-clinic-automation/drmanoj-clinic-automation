#!/bin/bash
# =====================================================================
#  S195_ENTRY — retire the old Daily Sale page for stale/typed URLs
#
#  Makes /finance/entry redirect to the role's live page (maker ->
#  /finance/daily v2, checker -> /finance/review). The OLD single-page
#  entry stays reachable ONLY via /finance/entry?legacy=1. Nothing else
#  in finance_app.py changes.
#
#  Currency-gated: only patches the exact live S194E file (md5
#  d2863c30...). Backs up, compiles, restarts, smoke-tests, and ROLLS
#  BACK automatically if the service does not come back healthy.
# =====================================================================
set -u
DEPLOY=/root/deploy
APP="$DEPLOY/finance_app.py"
SVC=clinic-finance
PORT=8106
LIVE_MD5=d2863c30ed0d3cc23126c7da13d9fe9b
cd "$(dirname "$0")"

echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }

echo "[2/6] currency gate — on-box finance_app.py must be the live S194E"
[ -f "$APP" ] || { echo "*** RED: $APP missing."; exit 1; }
GOT=$(md5sum "$APP" | awk '{print $1}')
if [ "$GOT" != "$LIVE_MD5" ]; then
  echo "*** RED: on-box finance_app.py md5 = $GOT, expected $LIVE_MD5."
  echo "    The live app is not the version this patch was built against."
  echo "    STOPPING so nothing is clobbered. Tell Cowork the md5 above."
  exit 1
fi
echo "      OK ($GOT)"

echo "[3/6] backup + install"
cp "$APP" "$APP.bak_s195_entry" && echo "      backup: $APP.bak_s195_entry"
cp finance_app.py "$APP"
python3 -c "import py_compile;py_compile.compile('$APP',doraise=True)" || {
  echo '*** RED compile — rolling back'; cp "$APP.bak_s195_entry" "$APP"; exit 1; }

echo "[4/6] restart $SVC"
systemctl restart "$SVC"
sleep 3

echo "[5/6] smoke"
ACTIVE=$(systemctl is-active "$SVC" 2>/dev/null)
H=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 8 "http://127.0.0.1:$PORT/finance/healthz" 2>/dev/null)
E=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 8 "http://127.0.0.1:$PORT/finance/entry" 2>/dev/null)
echo "      service=$ACTIVE  healthz=$H  entry=$E"
OK=1
[ "$ACTIVE" = "active" ] || OK=0
case "$H" in 200|301|302|401|403) ;; *) OK=0;; esac   # app responding (not 000/5xx)
case "$E" in 200|301|302|401|403) ;; *) OK=0;; esac
if [ "$OK" != "1" ]; then
  echo "*** RED smoke — rolling back to $APP.bak_s195_entry"
  cp "$APP.bak_s195_entry" "$APP"; systemctl restart "$SVC"; sleep 2
  echo "    rolled back. service now: $(systemctl is-active "$SVC")"
  exit 1
fi

echo "[6/6] GREEN — /finance/entry now redirects to the role's live page."
echo "      Old page still at /finance/entry?legacy=1 . Backup kept."
echo "      Quick check in a browser as reception: open /finance/entry -> should"
echo "      land on /finance/daily (v2)."
