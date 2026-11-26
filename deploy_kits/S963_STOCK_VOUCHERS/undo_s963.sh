#!/bin/bash
# undo_s963.sh -- S963_STOCK_VOUCHERS: the three backups back (each checked against its FROM pin first), the new reader removed,
# clinic-finance restarted. REFUSES when a live file is no longer at this kit's TO pin (a later kit changed it: undoing would wipe that
# kit's work -- cold review S5). Takes the build lock and the collector's lock. The voucher tables and views stay in finance.db.
#    bash /root/deploy/repo/deploy_kits/S963_STOCK_VOUCHERS/undo_s963.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; MLOCK="${MLOCK:-/tmp/marg_ingest.lock}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; FIN_PORT="${FIN_PORT:-8106}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
from_of() { case "$1" in marg_ingest/signatures.json) echo 50ca61f470da66dcc7b22f32f9740190;; marg_ingest/marg_take.py) echo bc621caf202de958517cd5e8d9c25290;;
  marg_ingest/marg_ingest.py) echo b11099ffdf66f6fd78409cecd36a1ec5;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
NAMES="marg_ingest/signatures.json marg_ingest/marg_take.py marg_ingest/marg_ingest.py"
for n in $NAMES marg_ingest/marg_vouchers.py; do t=$(to_of "$n")
  [ "$(m5 "$ROOT/$n")" = "$t" ] || { echo "!! $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), not this kit's ${t:0:8} - a later change; nothing undone. Tell Claude."; exit 1; }; done
for n in $NAMES; do f=$(from_of "$n"); b="$ROOT/$n.bak_S963_${f:0:8}"
  [ "$(m5 "$b")" = "$f" ] || { echo "!! the backup $b is missing or not ${f:0:8} - nothing undone. Tell Claude."; exit 1; }; done
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S963 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
exec 9>>"$MLOCK"; flock -w "${MWAIT:-120}" 9 || { rm -f "$LOCK/owner"; rmdir "$LOCK"; echo "!! the collector's lock was not free - nothing undone. Run it again."; exit 1; }
for n in signatures.json marg_ingest.py marg_take.py; do f=$(from_of "marg_ingest/$n"); \cp -p "$ROOT/marg_ingest/$n.bak_S963_${f:0:8}" "$ROOT/marg_ingest/$n"; done
rm -f "$ROOT/marg_ingest/marg_vouchers.py"
"$SYSTEMCTL" restart "$FSVC"
flock -u 9; exec 9>&-
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done
rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null
for n in $NAMES; do f=$(from_of "$n"); echo "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
echo "   marg_vouchers.py present: $([ -e "$ROOT/marg_ingest/marg_vouchers.py" ] && echo yes || echo no) (expected no); finance healthz $h"
[ "$h" = 200 ] || { echo "!! finance healthz $h after the restart - send a photo of this screen to Claude."; exit 1; }
echo "S963 UNDONE."
