#!/bin/bash
# undo_s867.sh -- S867 taken away: the two files back to their FROM pins (each backup checked; each live file must be S867's), clinic-finance
# restarted. Words only were changed; nothing in the database was written by S867, so nothing else to undo.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
FILES="scan_register.py purchase_app.py"
declare -A FROM=([scan_register.py]=1aec54b4a29cac99a5cfad77d0c2d00f [purchase_app.py]=73e46df04dc6ed63c92e917ad305bf49)
to() { awk -v f="finance/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "$(to "$f")" ] || { echo "!! $ROOT/finance/$f is not at S867's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }; done
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f.bak_S867_${FROM[$f]:0:8}")" = "${FROM[$f]}" ] || { echo "!! the backup of $f is not at ${FROM[$f]:0:8} - nothing undone. Tell Claude."; exit 1; }; done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s867 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for f in $FILES; do \cp -p "$ROOT/finance/$f.bak_S867_${FROM[$f]:0:8}" "$ROOT/finance/$f" || { echo "!! could not put $f back"; exit 1; }; done
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S867 UNDONE: two files back at their FROM pins; finance healthz $h. The payment sheet says 'your Confirm' again."
