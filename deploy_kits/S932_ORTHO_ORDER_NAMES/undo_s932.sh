#!/bin/bash
# undo_s932.sh -- kit S932_ORTHO_ORDER_NAMES: the two files back to their FROM pins from the install's own backups; clinic-finance restarted.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
NAMES=("finance/order_sheet.py" "finance/porders.py"); FROMS=("85ce21480858bae6c373fb218e64ffc2" "ea014fbd9b90c81244e52940b10adf27")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
n=0
for k in 0 1; do b="$ROOT/${NAMES[$k]}.bak_S932_${FROMS[$k]:0:8}"
  if [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ]; then echo "   ${NAMES[$k]} already at its FROM pin"; continue; fi
  [ -f "$b" ] && [ "$(m5 "$b")" = "${FROMS[$k]}" ] || { echo "!! no backup at $b with the FROM pin - stop, nothing changed"; exit 1; }
  \cp -p "$b" "$ROOT/${NAMES[$k]}" && [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ] || { echo "!! could not put ${NAMES[$k]} back"; exit 1; }
  n=$((n+1)); done
[ "$n" = 0 ] && { echo "S932 undo: nothing to do"; exit 0; }
"$SYSTEMCTL" restart "$FSVC"; sleep 4
echo "S932 undo: $n file(s) back; finance healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")"
