#!/bin/bash
# undo_s927.sh · kit S927_HUB_NEEDS_YOU_INLINE: the four patched files back to their FROM bytes (each only when still at the kit's TO),
# clinic-finance restarted. hub_panels.py is left in place (unmounted once sanjeevni_day.py is back); hub_seen and Amir's jobs stay, harmless.
#    bash /root/deploy/repo/deploy_kits/S927_HUB_NEEDS_YOU_INLINE/undo_s927.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S927 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
NAMES=("finance/sanjeevni_day.py" "finance/sanjeevni_approvals.py" "finance/stock_watch.py" "finance/finance_ui/finance_approvals.html")
FROMS=("69c2921e69996f5524237e23d289d648" "a1a09d243b483bb5ec299460c67a23bd" "1a8c98c6c11f5d33d415b3c485bdc918" "f00db25df9315b427cf0eb7c1b2b9283")
did=0
for k in 0 1 2 3; do
  F="$ROOT/${NAMES[$k]}"; FROM="${FROMS[$k]}"; TO="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; B="$F.bak_S927_${FROM:0:8}"; c="$(m5 "$F")"
  if [ "$c" = "$FROM" ]; then echo "   ${NAMES[$k]} already at ${FROM:0:8}"
  elif [ "$c" != "$TO" ]; then echo "!! ${NAMES[$k]} is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."
  elif [ "$(m5 "$B")" != "$FROM" ]; then echo "!! the backup $B is missing or changed; ${NAMES[$k]} left as it is. Tell Claude."
  else \cp -p "$B" "$F" && [ "$(m5 "$F")" = "$FROM" ] && { echo "   ${NAMES[$k]} back to ${FROM:0:8}"; did=1; } || echo "!! could not put ${NAMES[$k]} back"; fi
done
if [ "$did" = 1 ]; then "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"; fi
echo "S927 undo: done."
