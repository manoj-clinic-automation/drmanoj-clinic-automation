#!/bin/bash
# undo_s898.sh -- kit S898: the three files back to their FROM bytes (only if each is still at its TO pin), clinic-finance restarted.
#   bash /root/deploy/repo/deploy_kits/S898_PHONE_STUCK_AND_SILENT/undo_s898.sh
# Messages already sent again or removed stay as they are (each is in audit_log).
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
NAMES=("finance/supplier_msg.py" "finance/porders_s454.py" "finance/finance_ui/finance_approvals.html")
FROMS=("bdfe4ce75ca0930b92ecd4fd960723cd" "c992ba910315200293fdd7273ebbfacb" "f045686d8f53535184bbb64758165118")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S898 undo $(date '+%F %T')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for k in 0 1 2; do
  n="${NAMES[$k]}"; t="$(awk -v f="$n" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; b="$ROOT/$n.bak_S898_${FROMS[$k]:0:8}"; c="$(m5 "$ROOT/$n")"
  if [ "$c" = "${FROMS[$k]}" ]; then echo "-- $n already at its old version"; continue; fi
  [ "$c" = "$t" ] || { echo "!! $n is ${c:0:8}, neither the kit's nor the old -- changed since; nothing undone for it. Tell Claude."; continue; }
  [ "$(m5 "$b")" = "${FROMS[$k]}" ] || { echo "!! the backup of $n is missing or changed - nothing undone for it. Tell Claude."; continue; }
  \cp -p "$b" "$ROOT/$n" && echo "-- $n back to ${FROMS[$k]:0:8}"
done
"$SYSTEMCTL" restart "$FSVC" && echo "S898 UNDONE: $FSVC restarted."
