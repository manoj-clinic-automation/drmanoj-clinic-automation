#!/bin/bash
# undo_s965.sh · kit S965_VOUCHER_JUDGE: the four files back to their FROM (each only when still at the kit's TO), voucher_judge.py set aside,
# clinic-finance restarted. The name table mi_voucher_name and the restamped 'exported' times stay (nothing reads the first; the second only
# orders a retried sheet by its export). S963 / S964 stay.
#    bash /root/deploy/repo/deploy_kits/S965_VOUCHER_JUDGE/undo_s965.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; MLOCK="${MLOCK:-/tmp/marg_ingest.lock}"
FILES=("finance/stock_check.py 26665c78e59ecf4872a21eedbda7b531" "finance/stock_check.html 13e348a97a25c51fdff8ef9ddc5122a5"
       "finance/item_ledger.py d2f68ee900dfbcb40a25f570f6782c58" "marg_ingest/marg_vouchers.py 923180680678a0480c1b2d1a1300830a"
       "finance/voucher_judge.py NEW")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S965 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; c="$(m5 "$f")"
  if [ "$fr" = NEW ]; then [ -z "$c" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- not the kit's; nothing undone. Tell Claude."; exit 1; }; continue; fi
  [ "$c" = "$fr" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- neither the kit's TO nor its FROM; nothing undone. Tell Claude."; exit 1; }
  [ "$c" = "$fr" ] || [ "$(m5 "$f.bak_S965_${fr:0:8}")" = "$fr" ] || { echo "!! the backup of $n is missing or changed; nothing undone. Tell Claude."; exit 1; }; done
exec 9>>"$MLOCK"; flock -w 120 9 || { echo "!! the Marg collection holds its lock - nothing undone. Run it again in five minutes."; exit 3; }
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"
  if [ "$fr" = NEW ]; then [ -f "$f" ] && mv -f "$f" "$f.bak_S965_undone" && echo "   $n set aside"; continue; fi
  if [ "$(m5 "$f")" = "$fr" ]; then echo "   $n already at ${fr:0:8}"; continue; fi
  \cp -p "$f.bak_S965_${fr:0:8}" "$f" && [ "$(m5 "$f")" = "$fr" ] && echo "   $n back to ${fr:0:8}" || { echo "!! could not put $n back. Tell Claude."; exit 1; }; done
flock -u 9; exec 9>&-
"$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"
echo "S965 UNDONE."
