#!/bin/bash
# undo_s956.sh · kit S956_SAME_DAY_DELIVERY: stock_figure.py back to S952's 500a7d46 (only when still at the kit's TO), clinic-finance restarted,
# the stock of record rebuilt by the old code. S952 and S954 stay.
#    bash /root/deploy/repo/deploy_kits/S956_SAME_DAY_DELIVERY/undo_s956.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S956 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
F="$ROOT/finance/stock_figure.py"; FROM8="500a7d46"; TO="$(awk '$2=="finance/stock_figure.py"{print $1}' "$KDIR/TO_PINS.md5")"; B="$F.bak_S956_$FROM8"; c="$(m5 "$F")"
if [ "${c:0:8}" = "$FROM8" ]; then echo "   finance/stock_figure.py already at $FROM8"; echo "S956 undo: done."; exit 0; fi
[ "$c" = "$TO" ] || { echo "!! finance/stock_figure.py is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."; exit 1; }
[ "$(m5 "$B" | cut -c1-8)" = "$FROM8" ] || { echo "!! the backup $B is missing or changed; left as it is. Tell Claude."; exit 1; }
\cp -p "$B" "$F" && [ "$(m5 "$F" | cut -c1-8)" = "$FROM8" ] && echo "   finance/stock_figure.py back to $FROM8" || { echo "!! could not put it back"; exit 1; }
"$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"
echo "   the stock of record rebuilt by the old code: $(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" timeout 900 "$VPY" -W ignore -B "$ROOT/finance/stock_record.py" --build --force 2>&1 | tail -1 | cut -c1-80)"
echo "S956 undo: done."
