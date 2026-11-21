#!/bin/bash
# undo_s921.sh · kit S921_PURCHASE_FLOW_2: the four files back to their FROM bytes (each only when still at the kit's TO), the F-1547
# messages back to 'skipped' (by the ids the install kept), clinic-finance restarted. Her word (order_flow_rec) stays, read by nothing.
#    bash /root/deploy/repo/deploy_kits/S921_PURCHASE_FLOW_2/undo_s921.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S921 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
NAMES=("finance/order_flow.py" "finance/porders_s454.py" "finance/order_s778.py" "finance/porders.html")
FROMS=("f4ce2c934f410944cf1816adb59f143b" "cdb9b65f9919a2203207771d074a4a6e" "10842db6389c010e0fbe87f6c9369819" "cbe1a46a72e0e82489c00397e303daab")
did=0
for k in 0 1 2 3; do
  F="$ROOT/${NAMES[$k]}"; FROM="${FROMS[$k]}"; TO="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; B="$F.bak_S921_${FROM:0:8}"; c="$(m5 "$F")"
  if [ "$c" = "$FROM" ]; then echo "   ${NAMES[$k]} already at ${FROM:0:8}"
  elif [ "$c" != "$TO" ]; then echo "!! ${NAMES[$k]} is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."
  elif [ "$(m5 "$B")" != "$FROM" ]; then echo "!! the backup $B is missing or changed; ${NAMES[$k]} left as it is. Tell Claude."
  else \cp -p "$B" "$F" && [ "$(m5 "$F")" = "$FROM" ] && { echo "   ${NAMES[$k]} back to ${FROM:0:8}"; did=1; } || echo "!! could not put ${NAMES[$k]} back"; fi
done
IDS="$ROOT/finance/.s921_f1547_ids.txt"
if [ -f "$IDS" ]; then
  (cd /tmp && "$VPY" - "$LIVE_DB" "$IDS" <<'PYEOF'
import re, sqlite3, sys
ids = [int(x) for x in re.findall(r"ids=([\d,]*)", open(sys.argv[2]).read())[0].split(",") if x]
con = sqlite3.connect(sys.argv[1], timeout=30)
n = 0
for i in ids:
    n += con.execute("UPDATE supplier_msg SET status='skipped', sent_at=NULL, sent_by=NULL, last_error=substr(last_error, instr(last_error, 'Was: ') + 5) "
                     "WHERE id=? AND sent_by='S921 (F-1547)'", (i,)).rowcount
con.commit()
print("   F-1547: %d messages back to skipped" % n)
PYEOF
  ) && mv -f "$IDS" "$IDS.undone_$(date +%Y%m%d_%H%M%S)"
fi
if [ "$did" = 1 ]; then "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"; fi
echo "S921 undo: done."
