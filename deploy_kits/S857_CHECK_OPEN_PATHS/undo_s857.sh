#!/bin/bash
# undo_s857.sh -- S857 taken away: scan_register.py and month_asks.py back to their FROM pins (S855's; each backup checked; each live file must be
# S857's), clinic-finance restarted.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
FILES="scan_register.py month_asks.py"
declare -A FROM=([scan_register.py]=95c5ad0e42b957de37a60f16eb335d73 [month_asks.py]=d0592c402c4838d8fe2fa311220de4e1)
to() { awk -v f="finance/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "$(to "$f")" ] || { echo "!! $ROOT/finance/$f is not at S857's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }; done
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f.bak_S857_${FROM[$f]:0:8}")" = "${FROM[$f]}" ] || { echo "!! the backup of $f is not at ${FROM[$f]:0:8} - nothing undone. Tell Claude."; exit 1; }; done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s857 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for f in $FILES; do \cp -p "$ROOT/finance/$f.bak_S857_${FROM[$f]:0:8}" "$ROOT/finance/$f" || { echo "!! could not put $f back"; exit 1; }; done
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S857 UNDONE: two files back at their FROM pins; finance healthz $h"
