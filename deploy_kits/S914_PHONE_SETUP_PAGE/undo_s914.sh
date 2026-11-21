#!/bin/bash
# undo_s914.sh · kit S914_PHONE_SETUP_PAGE: both files back to their FROM bytes (only when they are still at the kit's TO), clinic-finance restarted.
#    bash /root/deploy/repo/deploy_kits/S914_PHONE_SETUP_PAGE/undo_s914.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
NAMES=("finance/supplier_msg.py" "finance/porders_s454.py")
FROMS=("77656157b038765d2b88f8ec28069b81" "0053ae60f8dc93d9301463ba69671aed")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S914 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
did=0
for k in 0 1; do
  n="${NAMES[$k]}"; to="$(awk -v f="$n" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; b="$ROOT/$n.bak_S914_${FROMS[$k]:0:8}"; c="$(m5 "$ROOT/$n")"
  if [ "$c" = "${FROMS[$k]}" ]; then echo "   $n already at ${FROMS[$k]:0:8}"; continue; fi
  [ "$c" = "$to" ] || { echo "!! $n is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."; continue; }
  [ "$(m5 "$b")" = "${FROMS[$k]}" ] || { echo "!! the backup $b is missing or changed; $n left as it is. Tell Claude."; continue; }
  \cp -p "$b" "$ROOT/$n" && [ "$(m5 "$ROOT/$n")" = "${FROMS[$k]}" ] && { echo "   $n back to ${FROMS[$k]:0:8}"; did=1; } || echo "!! could not put $n back"
done
if [ "$did" = 1 ]; then "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"; fi
echo "S914 undo: done."
