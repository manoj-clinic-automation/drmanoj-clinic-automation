#!/bin/bash
# undo_s883.sh -- S883_LEDGER_BATCHES: both files back to their FROM (from the installer's backups), clinic-finance restarted.
#   bash /root/deploy/repo/deploy_kits/S883_LEDGER_BATCHES/undo_s883.sh
# The table stock_batch_now stays (nothing reads it without the S883 page; the next S883 install refills it).
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
N1="finance/expiry_watch.py"; F1="1ed95b6cda37af1b1a279129119fae4a"; N2="finance/item_ledger.py"; F2="b4040d8fc2d09719b27747c9f6a51d26"
KDIR="$(cd "$(dirname "$0")" && pwd)"
T1="$(awk -v f="$N1" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; T2="$(awk -v f="$N2" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
B1="$ROOT/$N1.bak_S883_${F1:0:8}"; B2="$ROOT/$N2.bak_S883_${F2:0:8}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
[ "$(m5 "$B1")" = "$F1" ] && [ "$(m5 "$B2")" = "$F2" ] || { echo "!! the backups are not at their FROM pins - nothing changed. Tell Claude."; exit 1; }
for x in "$N1:$T1:$F1" "$N2:$T2:$F2"; do n="${x%%:*}"; r="${x#*:}"; t="${r%%:*}"; f="${r#*:}"; c="$(m5 "$ROOT/$n")"
  [ "$c" = "$t" ] || [ "$c" = "$f" ] || { echo "!! $ROOT/$n is ${c:0:8} - neither S883's nor its FROM; nothing changed. Tell Claude."; exit 1; }; done
if ! mkdir "$LOCK" 2>/dev/null; then echo "!! another build holds the lock $LOCK - nothing changed. Run it again in five minutes."; exit 3; fi
echo "undo_s883 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
\cp -p "$B1" "$ROOT/$N1" && \cp -p "$B2" "$ROOT/$N2" || { echo "!! the copy back failed - send a photo to Claude"; exit 1; }
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done
echo "S883 undone: $N1 $(m5 "$ROOT/$N1" | cut -c1-8), $N2 $(m5 "$ROOT/$N2" | cut -c1-8); $FSVC restarted, finance healthz $h."
