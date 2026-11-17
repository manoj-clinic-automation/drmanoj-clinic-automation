#!/bin/bash
# undo_s855.sh -- S855 taken away: the four files back to their FROM pins (each backup checked; each live file must be S855's), month_asks.py
# withdrawn (renamed, never deleted), clinic-finance restarted. Bills it resolved stay Correct (each in purchase_audit).
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
FILES="purchase_app.py scan_register.py sanjeevni_approvals.py amir_day.py"
declare -A FROM=([purchase_app.py]=c54b1c315392d9c567f99bb1d589e008 [scan_register.py]=76ad0927829ef5d066101539834d1831 [sanjeevni_approvals.py]=960efdd342752b46bdecbc629bce533c [amir_day.py]=22d962b8ef68dbdbbfc3e576ff1a9060)
to() { awk -v f="finance/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
for f in $FILES month_asks.py; do [ "$(m5 "$ROOT/finance/$f")" = "$(to "$f")" ] || { echo "!! $ROOT/finance/$f is not at S855's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }; done
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f.bak_S855_${FROM[$f]:0:8}")" = "${FROM[$f]}" ] || { echo "!! the backup of $f is not at ${FROM[$f]:0:8} - nothing undone. Tell Claude."; exit 1; }; done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s855 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for f in $FILES; do \cp -p "$ROOT/finance/$f.bak_S855_${FROM[$f]:0:8}" "$ROOT/finance/$f" || { echo "!! could not put $f back"; exit 1; }; done
mv -f "$ROOT/finance/month_asks.py" "$ROOT/finance/month_asks.py.withdrawn_S855_$(date +%Y%m%d_%H%M%S)"
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S855 UNDONE: four files back at their FROM pins, month_asks.py withdrawn; finance healthz $h"
