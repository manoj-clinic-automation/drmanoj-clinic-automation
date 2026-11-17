#!/bin/bash
# undo_s849.sh -- S849 taken away: the five files back to their FROM pins (each backup checked; each live file must be S849's), scan_ask.py
# withdrawn (renamed, never deleted), clinic-finance restarted. The table s849_answer stays (nothing reads it without scan_ask.py).
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
FILES="sanjeevni_approvals.py amir_day.py purchase_app.py provisional_s781.py scan_register.py"
declare -A FROM=([sanjeevni_approvals.py]=7d75f9d51cbc14d4b3a2dd4d1668aef5 [amir_day.py]=c016278b8a4f9fb2aa42dbfe60008d26 [purchase_app.py]=d1999929730c394da5d00782c66e858e [provisional_s781.py]=4d9cef5543b4d983561a5518d8fc0feb [scan_register.py]=eb48202f1c6edbc2aa60a4ed211dd948)
to() { awk -v f="finance/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
for f in $FILES scan_ask.py; do [ "$(m5 "$ROOT/finance/$f")" = "$(to "$f")" ] || { echo "!! $ROOT/finance/$f is not at S849's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }; done
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f.bak_S849_${FROM[$f]:0:8}")" = "${FROM[$f]}" ] || { echo "!! the backup of $f is not at ${FROM[$f]:0:8} - nothing undone. Tell Claude."; exit 1; }; done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s849 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for f in $FILES; do \cp -p "$ROOT/finance/$f.bak_S849_${FROM[$f]:0:8}" "$ROOT/finance/$f" || { echo "!! could not put $f back"; exit 1; }; done
mv -f "$ROOT/finance/scan_ask.py" "$ROOT/finance/scan_ask.py.withdrawn_S849_$(date +%Y%m%d_%H%M%S)"
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S849 UNDONE: five files back at their FROM pins, scan_ask.py withdrawn; finance healthz $h"
