#!/bin/bash
# undo_s850.sh -- S850 taken away: the three files back to their FROM pins (each backup checked; each live file must be S850's), marg_right.py
# withdrawn (renamed, never deleted), clinic-finance restarted. The tables s850_tap and s850_correction stay (nothing reads them without marg_right.py).
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
FILES="scan_ask.py purchase_app.py item_ledger.py"
declare -A FROM=([scan_ask.py]=41adf66bceb6e7ef31f25181c8a2da71 [purchase_app.py]=b789e3791684743969bbf1d25e1b3f92 [item_ledger.py]=49768145965c2bbd81bdf56ab5ca9f74)
to() { awk -v f="finance/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
for f in $FILES marg_right.py; do [ "$(m5 "$ROOT/finance/$f")" = "$(to "$f")" ] || { echo "!! $ROOT/finance/$f is not at S850's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }; done
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f.bak_S850_${FROM[$f]:0:8}")" = "${FROM[$f]}" ] || { echo "!! the backup of $f is not at ${FROM[$f]:0:8} - nothing undone. Tell Claude."; exit 1; }; done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s850 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for f in $FILES; do \cp -p "$ROOT/finance/$f.bak_S850_${FROM[$f]:0:8}" "$ROOT/finance/$f" || { echo "!! could not put $f back"; exit 1; }; done
mv -f "$ROOT/finance/marg_right.py" "$ROOT/finance/marg_right.py.withdrawn_S850_$(date +%Y%m%d_%H%M%S)"
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S850 UNDONE: three files back at their FROM pins, marg_right.py withdrawn; finance healthz $h"
