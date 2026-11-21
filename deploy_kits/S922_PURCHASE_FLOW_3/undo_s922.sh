#!/bin/bash
# undo_s922.sh · kit S922_PURCHASE_FLOW_3: the three files back to their FROM bytes (each only when still at the kit's TO),
# clinic-finance restarted.
#    bash /root/deploy/repo/deploy_kits/S922_PURCHASE_FLOW_3/undo_s922.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S922 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
NAMES=("finance/order_flow.py" "finance/darpan_kal.py" "finance/darpan_kal.html")
FROMS=("47edf0626935b863f9654823f5baec5e" "5b055ed8829582a37669a883f0507f07" "1d87325139139db751fba8f928a3a7df")
did=0
for k in 0 1 2; do
  F="$ROOT/${NAMES[$k]}"; FROM="${FROMS[$k]}"; TO="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; B="$F.bak_S922_${FROM:0:8}"; c="$(m5 "$F")"
  if [ "$c" = "$FROM" ]; then echo "   ${NAMES[$k]} already at ${FROM:0:8}"
  elif [ "$c" != "$TO" ]; then echo "!! ${NAMES[$k]} is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."
  elif [ "$(m5 "$B")" != "$FROM" ]; then echo "!! the backup $B is missing or changed; ${NAMES[$k]} left as it is. Tell Claude."
  else \cp -p "$B" "$F" && [ "$(m5 "$F")" = "$FROM" ] && { echo "   ${NAMES[$k]} back to ${FROM:0:8}"; did=1; } || echo "!! could not put ${NAMES[$k]} back"; fi
done
if [ "$did" = 1 ]; then "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"; fi
echo "S922 undo: done."
