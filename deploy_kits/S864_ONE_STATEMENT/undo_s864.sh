#!/bin/bash
# undo_s864.sh -- S864 taken away: the four files back to their FROM pins (each backup checked; each live file must be S864's), clinic-finance
# restarted. The one-off's data stays as it is (each statement it retired and each Wrong mark it resolved is in purchase_audit, action
# s864_superseded / verdict_resolved); nothing is deleted. The old code reads the figures exactly as before S864 for every month.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
FILES="purchase_app.py month_asks.py amir_day.py export_watch.py"
declare -A FROM=([purchase_app.py]=1ac9d1efae26a8b3bd6e61d4cb9a0324 [month_asks.py]=cf72cde93e65afee567ae854be193c43 [amir_day.py]=97e56bc73a047ed1fe4fd3ef93dec5f6 [export_watch.py]=f6845ec5ae1dc8fe200ebf5f4c3ad173)
to() { awk -v f="finance/$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f")" = "$(to "$f")" ] || { echo "!! $ROOT/finance/$f is not at S864's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }; done
for f in $FILES; do [ "$(m5 "$ROOT/finance/$f.bak_S864_${FROM[$f]:0:8}")" = "${FROM[$f]}" ] || { echo "!! the backup of $f is not at ${FROM[$f]:0:8} - nothing undone. Tell Claude."; exit 1; }; done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s864 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for f in $FILES; do \cp -p "$ROOT/finance/$f.bak_S864_${FROM[$f]:0:8}" "$ROOT/finance/$f" || { echo "!! could not put $f back"; exit 1; }; done
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S864 UNDONE: four files back at their FROM pins; finance healthz $h. The one-off's retired statements and resolved Wrong marks stay (audited); the old code shows the figures as before."
