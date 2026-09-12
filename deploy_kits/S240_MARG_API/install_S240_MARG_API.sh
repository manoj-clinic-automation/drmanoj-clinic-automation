#!/bin/bash
# =============================================================================
#  install_S240_MARG_API.sh · kit S240_MARG_API · D467 phase 2b (the machine door)
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_MARG_API
#
#  The medical PC can now push each capture the moment it is taken:
#      GET  /finance/api/marg-file    "are you there?"
#      POST /finance/api/marg-file    one export -> TAKEN / ALREADY / REFUSED / BUSY
#  Same marg_take.take() as the browser page and the 5-minute collector: de-duplicated by the
#  file's own md5, same router, same PHI rule. NO NEW SECRET -- it uses FINANCE_MARG_TOKEN, the
#  scoped stage-only key the medical PC already holds, and that key opens this path and no other.
#
#  Two edits: marg_door.py is replaced, and ONE line is added to the app's token tuple. Both are
#  backed up; if the app does not come back, or any probe fails, both are put back and the
#  service restarted. The key is never printed.  Needs S240_MARG_DOOR already installed.
# =============================================================================
set -u
KIT="S240_MARG_API"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${MI_PY:-/root/wa/venv/bin/python3}"
APY="${APP_PY:-/usr/bin/python3}"
DEST="${MI_DEST:-/root/marg_ingest}"
FIN="${FINANCE_DIR:-/root/finance}"
FA="$FIN/finance_app.py"
SVC="${FIN_SVC:-clinic-finance.service}"
PORT="${FIN_PORT:-8106}"
DOOR_PIN_OLD="8ba1f586ed9f7d897639fc5efca7a2f9"
FA_BAK=""
DOOR_BAK=""
CFG=""
trap '[ -n "$CFG" ] && rm -f "$CFG"' EXIT
red() { echo "!! RED -- $*"; exit 1; }

rollback() {
  [ -n "$DOOR_BAK" ] && [ -f "$DOOR_BAK" ] && \cp -f "$DOOR_BAK" "$FIN/marg_door.py"
  [ -n "$FA_BAK" ] && [ -f "$FA_BAK" ] && \cp -f "$FA_BAK" "$FA"
  systemctl restart "$SVC"; sleep 4
  systemctl is-active --quiet "$SVC" && echo "   both files put back and the service is up again"
  red "$*"
}

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum marg_door.py | awk '{print $1}')" ] \
  || red "KIT_ID does not match marg_door.py (F-88)"
[ -x "$PY" ] || red "$PY not found"
[ -x "$APY" ] || red "$APY not found"
[ -f "$FA" ] || red "$FA is not there"
[ -f "$DEST/marg_take.py" ] || red "$DEST/marg_take.py is not there -- install S240_MARG_DOOR first"
[ -f "$FIN/marg_door.py" ] || red "$FIN/marg_door.py is not there -- install S240_MARG_DOOR first"
LIVE_DOOR="$(md5sum "$FIN/marg_door.py" | awk '{print $1}')"
NEW_DOOR="$(md5sum marg_door.py | awk '{print $1}')"
if [ "$LIVE_DOOR" != "$DOOR_PIN_OLD" ] && [ "$LIVE_DOOR" != "$NEW_DOOR" ]; then
  red "live marg_door.py is ${LIVE_DOOR:0:8}, neither S240_MARG_DOOR's nor this kit's -- nothing changed"
fi
grep -q "S240_MARG_DOOR begin" "$FA" || red "marg_door is not mounted in $FA -- install S240_MARG_DOOR first"
echo "-- gates green; live marg_door.py ${LIVE_DOOR:0:8}"

# the key, read from the service and NEVER printed ------------------------------------------
TOK="$(systemctl show -p Environment --value "$SVC" 2>/dev/null | tr ' ' '\n' | sed -n 's/^FINANCE_MARG_TOKEN=//p' | head -1)"
[ -n "$TOK" ] || red "FINANCE_MARG_TOKEN is not set on this box, so the medical PC's key would open nothing. Nothing was changed."
CFG="$(mktemp)"; chmod 600 "$CFG"
printf 'header = "X-Finance-Marg: %s"\n' "$TOK" > "$CFG"
TOK=""
echo "-- the pharmacy key is set on this service (its value is not printed, here or anywhere)"

# 1. the new door file -----------------------------------------------------------------------
if [ "$LIVE_DOOR" != "$NEW_DOOR" ]; then
  DOOR_BAK="$FIN/marg_door.py.bak_${KIT}_${LIVE_DOOR:0:8}"
  \cp -f "$FIN/marg_door.py" "$DOOR_BAK" || red "backup of marg_door.py"
fi
\cp -f marg_door.py "$FIN/marg_door.py" || red "copy marg_door.py"
"$APY" -m py_compile "$FIN/marg_door.py" || rollback "marg_door.py does not compile under $APY"
rm -rf "$FIN/__pycache__/marg_door.cpython-"*.pyc 2>/dev/null
echo "-- marg_door.py ${LIVE_DOOR:0:8} -> ${NEW_DOOR:0:8}"

# 2. one line in the app's token tuple --------------------------------------------------------
OUT="$(FA_PATH="$FA" "$PY" -B "$KDIR/patch_finance_app_S240_api.py" 2>&1)" \
  || { echo "$OUT"; rollback "the gate edit refused -- nothing was changed"; }
echo "$OUT" | sed 's/^/   /'
FA_BAK="$(echo "$OUT" | awk -F': *' '/backup +:/{print $2}')"

# 3. restart, then prove the door from outside, end to end ------------------------------------
systemctl restart "$SVC"; sleep 4
systemctl is-active --quiet "$SVC" || rollback "$SVC did not come back"
U="localhost:$PORT/finance/api/marg-file"
HZ="$(curl -s -o /dev/null -w '%{http_code}' "localhost:$PORT/finance/healthz")"
[ "$HZ" = "200" ] || rollback "healthz is not 200"
NOKEY="$(curl -s -o /dev/null -w '%{http_code}' "$U")"
READY="$(curl -s -K "$CFG" "$U")"
RC_READY="$(curl -s -K "$CFG" -o /dev/null -w '%{http_code}' "$U")"
echo "-- without the key: $NOKEY (401 = shut)   ·   with it: $RC_READY"
echo "   $(echo "$READY" | head -c 200)"
[ "$NOKEY" = "401" ] || rollback "the door answered $NOKEY without a key -- it must be 401"
[ "$RC_READY" = "200" ] || rollback "the door answered $RC_READY with the key"

SAMPLE="$(find "$DEST/archive" -type f \( -name '*.XLS' -o -name '*.xls' -o -name '*.xlsx' \) | head -1)"
if [ -n "$SAMPLE" ]; then
  M5="$(md5sum "$SAMPLE" | awk '{print $1}')"
  R1="$(curl -s -K "$CFG" -F "f=@$SAMPLE" -F "md5=$M5" -F "source=test" "$U")"
  S1="$(echo "$R1" | grep -o '"status":[ ]*"[A-Z_]*"' | head -1)"
  echo "-- a real export sent through the door: $S1"
  case "$R1" in *'"ALREADY"'*|*'"TAKEN"'*) : ;; *) rollback "the door did not take a real export: $(echo "$R1" | head -c 160)" ;; esac
  R2="$(curl -s -o /dev/null -w '%{http_code}' -K "$CFG" -F "f=@$SAMPLE" -F "md5=00000000000000000000000000000000" "$U")"
  echo "-- the same file with a wrong md5 declared: $R2 (400 = refused, as it must be)"
  [ "$R2" = "400" ] || rollback "a file whose md5 did not match was not refused (answered $R2)"
else
  echo "-- NOTE: no export file in $DEST/archive to send through the door; the send path was not exercised"
fi
UP="$(curl -s -o /dev/null -w '%{http_code}' "localhost:$PORT/finance/clinic/marg/upload")"
echo "-- the browser page is still there: $UP (302/200 = mounted and gated)"
case "$UP" in 200|302|303|401|403) : ;; *) rollback "the upload page answered $UP" ;; esac

echo
echo "PINS  $FIN/marg_door.py   $(md5sum "$FIN/marg_door.py" | awk '{print $1}')"
echo "      $FA  $(md5sum "$FA" | awk '{print $1}')"
echo
echo "$KIT GREEN -- the server will now take a Marg export from the medical PC the moment it is made."
echo "Next: the medical PC's side, delivered through Drive as one double-click."
