#!/bin/bash
# undo_s872.sh -- S872_HUB_TWO_TAP taken away: the page's backup back (checked against its FROM pin first), clinic-finance restarted.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
N="finance/finance_ui/finance_approvals.html"; FR="7253dc9f9a8ec0cfd576808af4c9b6a7"; TO=$(awk -v f="$N" '$2==f{print $1}' "$KD/TO_PINS.md5")
[ "$(m5 "$ROOT/$N")" = "$TO" ] || { echo "!! $ROOT/$N is not at S872's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s872 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
B="$ROOT/$N.bak_S872_${FR:0:8}"; [ "$(m5 "$B")" = "$FR" ] || { echo "!! the backup $B is not at its FROM pin - nothing changed. Tell Claude."; exit 1; }
\cp -p "$B" "$ROOT/$N" || { echo "!! could not put the page back"; exit 1; }
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S872 UNDONE: finance_approvals.html $(m5 "$ROOT/$N" | cut -c1-8) (S869's page back); finance healthz $h"
