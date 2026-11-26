#!/bin/bash
# undo_s964.sh -- S964_VOUCHER_NAME_SHAPE: the S963 reader back (checked against its pin), clinic-finance restarted. Refuses when the live
# reader is not this kit's (a later change). The cleared record is not put back (the collection has taken the sheet again).
#    bash /root/deploy/repo/deploy_kits/S964_VOUCHER_NAME_SHAPE/undo_s964.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; MLOCK="${MLOCK:-/tmp/marg_ingest.lock}"
N="marg_ingest/marg_vouchers.py"; FROM="7bc3df848ff4a8fdb5ba6d978d4496c0"; TO="$(awk -v f="$N" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
B="$ROOT/$N.bak_S964_${FROM:0:8}"
[ "$(m5 "$ROOT/$N")" = "$TO" ] || { echo "!! $ROOT/$N is not this kit's ${TO:0:8} - nothing undone. Tell Claude."; exit 1; }
[ "$(m5 "$B")" = "$FROM" ] || { echo "!! the backup $B is missing or not ${FROM:0:8} - nothing undone. Tell Claude."; exit 1; }
exec 9>>"$MLOCK"; flock -w "${MWAIT:-120}" 9 || { echo "!! the collector's lock was not free - nothing undone"; exit 1; }
cat "$B" > "$ROOT/marg_ingest/.marg_vouchers.py.u964" && mv -f "$ROOT/marg_ingest/.marg_vouchers.py.u964" "$ROOT/$N"
"$SYSTEMCTL" restart "$FSVC"; flock -u 9
echo "   $N $(m5 "$ROOT/$N" | cut -c1-8) (expected ${FROM:0:8})"
echo "S964 UNDONE."
