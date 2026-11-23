#!/bin/bash
# undo_s939.sh · kit S939_ORDER_FINAL: the flow switched off (order.d1053 = 0), the three files back to their FROM bytes (each only when
# still at the kit's TO), the new order_d1053.py moved aside, clinic-finance restarted. The kit's own tables stay (unused).
#    bash /root/deploy/repo/deploy_kits/S939_ORDER_FINAL/undo_s939.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S939 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
(cd /tmp && "$VPY" -W ignore -B "$KDIR/s939_on.py" "$KDIR" "$LIVE_DB" off) || echo "!! the switch could not be set off - the files are put back anyway"
NAMES=("finance/porders_s454.py" "finance/darpan_kal.py" "finance/darpan_kal.html")
FROMS=("e98e5ed08f861ff3e92ea7fd815cba0f" "64ce53b75024916d67ec78110c8b1198" "3c30f22dd797aa4036452bc44eb3f78f")
did=0
for k in 0 1 2; do
  F="$ROOT/${NAMES[$k]}"; FROM="${FROMS[$k]}"; TO="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; B="$F.bak_S939_${FROM:0:8}"; c="$(m5 "$F")"
  if [ "$c" = "$FROM" ]; then echo "   ${NAMES[$k]} already at ${FROM:0:8}"
  elif [ "$c" != "$TO" ]; then echo "!! ${NAMES[$k]} is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."
  elif [ "$(m5 "$B")" != "$FROM" ]; then echo "!! the backup $B is missing or changed; ${NAMES[$k]} left as it is. Tell Claude."
  else \cp -p "$B" "$F" && [ "$(m5 "$F")" = "$FROM" ] && { echo "   ${NAMES[$k]} back to ${FROM:0:8}"; did=1; } || echo "!! could not put ${NAMES[$k]} back"; fi
done
N="$ROOT/finance/order_d1053.py"
if [ -f "$N" ]; then mv -f "$N" "$N.undone_S939" && { echo "   finance/order_d1053.py moved aside (.undone_S939)"; did=1; }; fi
if [ "$did" = 1 ]; then "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"; fi
echo "S939 undo: done."
