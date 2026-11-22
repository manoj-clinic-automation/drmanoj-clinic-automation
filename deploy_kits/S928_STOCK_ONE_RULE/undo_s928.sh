#!/bin/bash
# undo_s928.sh -- kit S928_STOCK_ONE_RULE: the two files back to their FROM pins from the install's own backups; clinic-finance restarted.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
NAMES=("finance/stock_figure.py" "finance/stock_watch.py"); FROMS=("cc1cef5dbc29694b2cf4de70b2dffc1a" "5acf3cf0ca8f927df5ef69bb804815f8")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
n=0
for k in 0 1; do b="$ROOT/${NAMES[$k]}.bak_S928_${FROMS[$k]:0:8}"
  if [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ]; then echo "   ${NAMES[$k]} already at its FROM pin"; continue; fi
  [ -f "$b" ] && [ "$(m5 "$b")" = "${FROMS[$k]}" ] || { echo "!! no backup at $b with the FROM pin - stop, nothing changed"; exit 1; }
  \cp -p "$b" "$ROOT/${NAMES[$k]}" && [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ] || { echo "!! could not put ${NAMES[$k]} back"; exit 1; }
  n=$((n+1)); done
[ "$n" = 0 ] && { echo "S928 undo: nothing to do"; exit 0; }
"$SYSTEMCTL" restart "$FSVC"; sleep 4
echo "S928 undo: $n file(s) back; finance healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")"
