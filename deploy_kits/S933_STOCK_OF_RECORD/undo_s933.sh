#!/bin/bash
# undo_s933.sh -- kit S933_STOCK_OF_RECORD: the four patched files back to their FROM pins from the install's backups; stock_record.py removed; the cron line out; clinic-finance restarted.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
NAMES=("finance/stock_figure.py" "finance/stock_check.py" "finance/stock_check.html" "finance/item_ledger.py"); FROMS=("8130315e01c7da5d24e1ba93f6e60ad8" "4211828933a4113e33b7553c8ac89b2d" "ae61a18cbfe7e9d1b75614dc16a7986c" "5fbb60200dc836a8a623fa7175bf0492")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
n=0
for k in 0 1 2 3; do b="$ROOT/${NAMES[$k]}.bak_S933_${FROMS[$k]:0:8}"
  if [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ]; then echo "   ${NAMES[$k]} already at its FROM pin"; continue; fi
  [ -f "$b" ] && [ "$(m5 "$b")" = "${FROMS[$k]}" ] || { echo "!! no backup at $b with the FROM pin - stop, nothing changed"; exit 1; }
  \cp -p "$b" "$ROOT/${NAMES[$k]}" && [ "$(m5 "$ROOT/${NAMES[$k]}")" = "${FROMS[$k]}" ] || { echo "!! could not put ${NAMES[$k]} back"; exit 1; }
  n=$((n+1)); done
[ -e "$ROOT/finance/stock_record.py" ] && { rm -f "$ROOT/finance/stock_record.py"; n=$((n+1)); echo "   finance/stock_record.py removed"; }
if crontab -l 2>/dev/null | grep -q '# S933_STOCK_OF_RECORD'; then B="$ROOT/finance/crontab.bak_S933undo_$(date +%Y%m%d_%H%M%S)"; crontab -l > "$B" 2>/dev/null
  if [ -s "$B" ] && [ "$(grep -c '' "$B")" -ge 10 ]; then grep -v '# S933_STOCK_OF_RECORD' "$B" | crontab - && { n=$((n+1)); echo "   the cron line removed (the crontab's copy: $B)"; }
  else echo "!! the crontab could not be read back whole - its S933 line is left in place; remove it by hand"; fi; fi
[ "$n" = 0 ] && { echo "S933 undo: nothing to do"; exit 0; }
"$SYSTEMCTL" restart "$FSVC"; sleep 4
echo "S933 undo: $n change(s) back; finance healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")"
