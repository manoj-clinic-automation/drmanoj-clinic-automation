#!/bin/bash
# undo_s847.sh -- S847 taken away: S845's page back (the backup checked against its pin; the live page must be S847's), clinic-finance restarted.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
N="$ROOT/finance/item_ledger.py"; FROM=22c24bd91e82f77cc34c5f4d27d8dc51; B="$N.bak_S847_${FROM:0:8}"
TO="$(awk '$2=="finance/item_ledger.py"{print $1}' "$KD/TO_PINS.md5")"
[ "$(m5 "$N")" = "$TO" ] || { echo "!! $N is not at S847's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }
[ "$(m5 "$B")" = "$FROM" ] || { echo "!! the backup $B is not at S845's pin ${FROM:0:8} - nothing undone. Tell Claude."; exit 1; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s847 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
\cp -p "$B" "$N" || { echo "!! could not put the page back"; exit 1; }
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S847 UNDONE: item_ledger.py $(m5 "$N" | cut -c1-8) (S845's ${FROM:0:8}); finance healthz $h"
