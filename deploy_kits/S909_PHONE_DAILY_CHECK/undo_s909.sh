#!/bin/bash
# undo_s909.sh -- kit S909: supplier_msg.py and porders_s454.py back to their FROM bytes (only if each is still at its TO pin),
# phone_check.py removed (only if at its TO pin), its cron line removed, clinic-finance restarted. Its two tables and settings stay (harmless).
#   bash /root/deploy/repo/deploy_kits/S909_PHONE_DAILY_CHECK/undo_s909.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; TAG="# S909_PHONE_CHECK"
NAMES=("finance/supplier_msg.py" "finance/porders_s454.py")
FROMS=("407d2b1d4cf7bda3bb28263bd55e0aa9" "06966a0f9262b1f87c1b608129d11848")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S909 undo $(date '+%F %T')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
if "$CRONTAB" -l 2>/dev/null | grep -qF "$TAG"; then "$CRONTAB" -l 2>/dev/null | grep -vF "$TAG" | "$CRONTAB" - && echo "-- the cron line removed"; else echo "-- no cron line"; fi
for k in 0 1; do
  n="${NAMES[$k]}"; t="$(awk -v f="$n" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; b="$ROOT/$n.bak_S909_${FROMS[$k]:0:8}"; c="$(m5 "$ROOT/$n")"
  if [ "$c" = "${FROMS[$k]}" ]; then echo "-- $n already at its old version"; continue; fi
  [ "$c" = "$t" ] || { echo "!! $n is ${c:0:8}, neither the kit's nor the old -- changed since; nothing undone for it. Tell Claude."; continue; }
  [ "$(m5 "$b")" = "${FROMS[$k]}" ] || { echo "!! the backup of $n is missing or changed - nothing undone for it. Tell Claude."; continue; }
  \cp -p "$b" "$ROOT/$n" && echo "-- $n back to ${FROMS[$k]:0:8}"
done
p="$ROOT/finance/phone_check.py"; t="$(awk '$2=="finance/phone_check.py"{print $1}' "$KDIR/TO_PINS.md5")"
if [ ! -f "$p" ]; then echo "-- finance/phone_check.py already gone"
elif [ "$(m5 "$p")" = "$t" ]; then mv -f "$p" "$p.removed_S909_$(date +%Y%m%d_%H%M%S)" && echo "-- finance/phone_check.py taken out (kept beside, renamed)"
else echo "!! finance/phone_check.py changed since the install - left in place. Tell Claude."; fi
DB="${DB:-$ROOT/finance/finance.db}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
"$VPY" -c 'import sqlite3,sys,datetime as d
c=sqlite3.connect(sys.argv[1],timeout=60)
try:
  a=c.execute("UPDATE supplier_msg SET status=\x27skipped\x27, last_error=\x27withdrawn by undo S909\x27 WHERE kind=\x27check\x27 AND status IN (\x27queued\x27,\x27failed\x27)").rowcount
  b=c.execute("UPDATE supplier_msg SET handed_at=NULL WHERE kind=\x27check\x27 AND status=\x27skipped\x27 AND handed_at>=?",((d.datetime.now()-d.timedelta(hours=25)).replace(microsecond=0).isoformat(),)).rowcount
  c.commit(); print("-- check messages withdrawn: %d; handed marks cleared: %d" % (a,b))
except sqlite3.Error as e: print("-- no check messages to withdraw (%s)" % e.__class__.__name__)' "$DB"
"$SYSTEMCTL" restart "$FSVC" && echo "S909 UNDONE: $FSVC restarted."
