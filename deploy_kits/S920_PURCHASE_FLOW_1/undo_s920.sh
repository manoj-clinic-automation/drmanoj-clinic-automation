#!/bin/bash
# undo_s920.sh · kit S920_PURCHASE_FLOW_1: porders.py back to its FROM bytes (only when still at the kit's TO), order_flow.py set aside
# (renamed, never deleted; its table order_flow_mark stays, read by nothing), clinic-finance restarted.
#    bash /root/deploy/repo/deploy_kits/S920_PURCHASE_FLOW_1/undo_s920.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S920 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
FROM=c495f81265b190284c148196850f5fb6; TO="$(awk '$2=="finance/porders.py"{print $1}' "$KDIR/TO_PINS.md5")"
P="$ROOT/finance/porders.py"; B="$P.bak_S920_${FROM:0:8}"; c="$(m5 "$P")"; did=0
if [ "$c" = "$FROM" ]; then echo "   porders.py already at ${FROM:0:8}"
elif [ "$c" != "$TO" ]; then echo "!! porders.py is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."
elif [ "$(m5 "$B")" != "$FROM" ]; then echo "!! the backup $B is missing or changed; porders.py left as it is. Tell Claude."
else \cp -p "$B" "$P" && [ "$(m5 "$P")" = "$FROM" ] && { echo "   porders.py back to ${FROM:0:8}"; did=1; } || echo "!! could not put porders.py back"; fi
F="$ROOT/finance/order_flow.py"
if [ -f "$F" ]; then mv -f "$F" "$F.removed_S920_$(date +%Y%m%d_%H%M%S)" && { echo "   order_flow.py set aside"; did=1; }; fi
if [ "$did" = 1 ]; then "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"; fi
echo "S920 undo: done."
