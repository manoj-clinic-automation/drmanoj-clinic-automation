#!/bin/bash
# =============================================================================
#  install_S718_STAFF20_INACTIVE.sh . kit S718 (06-Nov-2026, session S390, the parent) . F-1131, F-1132
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s718kit && cp -rp /root/deploy/repo/deploy_kits/S718_STAFF20_INACTIVE /tmp/s718kit && bash /tmp/s718kit/install_S718_STAFF20_INACTIVE.sh
#  (DRY=1 before bash: every gate and what would change; nothing written.)
#
#  The owner, 14:10 IST 06-Nov: staff 20 inactive from October -- "ok, paid and all his dues cleared".
#  Staff 20 is 'Arjun', who LEFT on 30-Sep (D824). S712 (06-Nov 08:43) wrongly moved his base pay to 3,500, meant for the new
#  cleaner Arjun Dev (D835, a different person). This kit:
#    /root/staff_master.csv            number 20 Arjun: base 3500 -> 3200 (as when he left), active Y -> N. One line; backup first.
#    staff_register.db, table staff    the active row named exactly 'Arjun', IF there is one: last working 30-Sep, inactive.
#  Refused unless September AND October are LOCKED (their pay is then frozen in the locked runs). No code, no restart.
#  Undo: the tool prints its backups; copy staff_master.csv.bak_S718_<time> back over /root/staff_master.csv.
# =============================================================================
set -u
KIT="S718_STAFF20_INACTIVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
SM="${SM:-/root/staff_master.csv}"
SRD="${SRD:-/root/staff_register}"
ATT="${ATT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
WALK_OK="WALK OK 32/32"
HAVE_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
echo "1. kit files: all match SUMS.md5"
if [ -z "${SKIP_CFG:-}" ]; then
  CM=$(cd "$ATT" && "$PY" -B -c "import att_config as c; print(c.STAFF_MASTER)" 2>/dev/null)
  [ "$CM" = "$SM" ] || stop "att_config.STAFF_MASTER is '$CM', not $SM"
  echo "2. the attendance report and the salary read $SM"
fi
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s718.py" "$KDIR/staff20_s718.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || stop "the walk is not green ($R)"
echo "3. the walk on made-up lists and registers: $R"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s718.py" "$KDIR/staff20_s718.py" --control 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control (an untouched list): $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
R=$(cd "$SRD" && "$PY" -B "$KDIR/staff20_s718.py" --master "$SM" --dir "$SRD" --dry 2>&1); RC=$?
echo "$R" | sed 's/^/   on the live list, DRY: /'
[ "$RC" = 0 ] || stop "the DRY run on the live list stopped (rc $RC)"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
R=$(cd "$SRD" && "$PY" -B "$KDIR/staff20_s718.py" --master "$SM" --dir "$SRD" 2>&1); RC=$?
echo "$R" | sed 's/^/4. /'
[ "$RC" = 0 ] || { echo "!! the step stopped (rc $RC). Send a photo of this screen to Claude."; exit 1; }
echo ""
echo "$KIT: DONE. Staff 20 (Arjun, left 30-Sep) is off the staff list from November; September and October stay as locked and paid."
