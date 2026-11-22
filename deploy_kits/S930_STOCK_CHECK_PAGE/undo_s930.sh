#!/bin/bash
# undo_s930.sh -- kit S930_STOCK_CHECK_PAGE: the three patched files back to their FROM pins from the install's backups; the two new files removed; clinic-finance restarted.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
NAMES=("finance/sanjeevni_day.py" "finance/stock_watch.py" "finance/finance_ui/finance_approvals.html"); FROMS=("c01bf05bd754c37b2f73d8d1e18b7091" "02727b0fba9d1dd030d15ae6a4811faa" "bc5d52c9aaf7df9ee5747e21083c8642")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
n=0
for k in 0 1 2; do b="$ROOT/${NAMES[$k]}.bak_S930_${FROMS[$k]:0:8}"
  if [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ]; then echo "   ${NAMES[$k]} already at its FROM pin"; continue; fi
  [ -f "$b" ] && [ "$(m5 "$b")" = "${FROMS[$k]}" ] || { echo "!! no backup at $b with the FROM pin - stop, nothing changed"; exit 1; }
  \cp -p "$b" "$ROOT/${NAMES[$k]}" && [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ] || { echo "!! could not put ${NAMES[$k]} back"; exit 1; }
  n=$((n+1)); done
for f in finance/stock_check.py finance/stock_check.html; do [ -e "$ROOT/$f" ] && { rm -f "$ROOT/$f"; n=$((n+1)); echo "   $f removed"; }; done
[ "$n" = 0 ] && { echo "S930 undo: nothing to do"; exit 0; }
"$SYSTEMCTL" restart "$FSVC"; sleep 4
echo "S930 undo: $n file(s) back; finance healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")"
