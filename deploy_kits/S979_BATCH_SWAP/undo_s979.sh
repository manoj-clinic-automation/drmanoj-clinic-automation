#!/bin/bash
# undo_s979.sh · kit S979_BATCH_SWAP: the three files back to their FROM (each only when still at the kit's TO), batch_swap.py moved aside,
# the crontab line out, clinic-finance restarted. The table expiry_swap_case stays (nothing reads it once the files are back).
#    bash /root/deploy/repo/deploy_kits/S979_BATCH_SWAP/undo_s979.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"; CRONTAB="${CRONTAB:-crontab}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FILES=("finance/expiry_watch.py 5db83cbcd25b57fdbd52ab3077623f21" "finance/stockmatch.py 91b5193ff21848274da94ef8dcebf82c"
       "finance/stockmatch.html bc67e10238047204e90df933773d3e08")
NEWF="finance/batch_swap.py"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S979 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; c="$(m5 "$f")"
  [ "$c" = "$fr" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- neither the kit's TO nor its FROM; nothing undone. Tell Claude."; exit 1; }
  [ "$c" = "$fr" ] || [ "$(m5 "$f.bak_S979_${fr:0:8}")" = "$fr" ] || { echo "!! the backup of $n is missing or changed; nothing undone. Tell Claude."; exit 1; }; done
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"
  if [ "$(m5 "$f")" = "$fr" ]; then echo "   $n already at ${fr:0:8}"; continue; fi
  \cp -p "$f.bak_S979_${fr:0:8}" "$f" && [ "$(m5 "$f")" = "$fr" ] && echo "   $n back to ${fr:0:8}" || { echo "!! could not put $n back. Tell Claude."; exit 1; }; done
if [ -f "$ROOT/$NEWF" ]; then mv -f "$ROOT/$NEWF" "$ROOT/$NEWF.undone_S979_$(date +%Y%m%d_%H%M%S)" && echo "   $NEWF moved aside"; fi
"$CRONTAB" -l 2>/dev/null | grep -v '# S979_BATCH_SWAP' | "$CRONTAB" - && echo "   the crontab line out ($("$CRONTAB" -l 2>/dev/null | grep -c '# S979_BATCH_SWAP') left)"
"$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"
echo "S979 UNDONE."
