#!/bin/bash
# undo_s845.sh -- S845_ITEM_LEDGER taken away: the two backups back (each checked against its FROM pin first), the new page removed,
# clinic-finance restarted. Nothing else was ever written by the kit.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
to_of() { awk -v f="$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
for n in finance/sanjeevni_approvals.py finance/finance_ui/finance_approvals.html; do
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || { echo "!! $ROOT/$n is not at S845's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }
done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s845 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for p in "finance/sanjeevni_approvals.py cd5174d6bfb9d62b55dd037e903e1d74" "finance/finance_ui/finance_approvals.html 9f6295856e36f93a00028de7cc3fe769"; do
  set -- $p; b="$ROOT/$1.bak_S845_${2:0:8}"
  [ "$(m5 "$b")" = "$2" ] || { echo "!! the backup $b is not at its FROM pin ${2:0:8} - nothing changed. Tell Claude."; exit 1; }
done
for p in "finance/sanjeevni_approvals.py cd5174d6bfb9d62b55dd037e903e1d74" "finance/finance_ui/finance_approvals.html 9f6295856e36f93a00028de7cc3fe769"; do
  set -- $p; \cp -p "$ROOT/$1.bak_S845_${2:0:8}" "$ROOT/$1" || { echo "!! could not put $1 back"; exit 1; }
done
rm -f "$ROOT/finance/item_ledger.py"
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S845 UNDONE: sanjeevni_approvals.py $(m5 "$ROOT/finance/sanjeevni_approvals.py" | cut -c1-8), finance_approvals.html $(m5 "$ROOT/finance/finance_ui/finance_approvals.html" | cut -c1-8), item_ledger.py present: $([ -e "$ROOT/finance/item_ledger.py" ] && echo yes || echo no); finance healthz $h"
