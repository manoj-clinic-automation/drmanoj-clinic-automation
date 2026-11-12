#!/bin/bash
# =============================================================================
#  install_S796_CALLBACK_CLOCK.sh . kit S796 (12-Nov-2026, session S435, the parent) . the owner 07:47 / 07:52 IST: a clock on the
#  call-back -- a missed caller not spoken to in 30 duty minutes is notified again to the phone staff, at 60 to Shavez (the backup),
#  and the count still open at closing time goes to the owner.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s796kit && cp -rp /root/deploy/repo/deploy_kits/S796_CALLBACK_CLOCK /tmp/s796kit && bash /tmp/s796kit/install_S796_CALLBACK_CLOCK.sh
#  NEW /root/portal/callback_clock.py + ONE cron line (every 5 minutes, 08:00-21:55). No live file changed, no restart.
#  Undo:  bash /tmp/s796kit/install_S796_CALLBACK_CLOCK.sh --undo
# =============================================================================
set -u
KIT="S796_CALLBACK_CLOCK"
TAG="# S796_CALLBACK_CLOCK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
CRONTAB="${CRONTAB:-crontab}"
N1="$ROOT/portal/callback_clock.py"; TON1=70eb11972362eee87a9f7d056e04cae5
export CC_CONSOLE_DB="${CC_CONSOLE_DB:-$ROOT/wa/console.db}"
export CC_REVIEWS_DB="${CC_REVIEWS_DB:-$ROOT/wa/console_reviews.db}"
export CC_STORE="${CC_STORE:-$ROOT/portal/callback_clock.db}"
LINE="*/5 8-21 * * * CC_CONSOLE_DB=$CC_CONSOLE_DB CC_REVIEWS_DB=$CC_REVIEWS_DB CC_STORE=$CC_STORE RING_PORTAL_DIR=$ROOT/portal $VPY -B $N1 >> $ROOT/portal/callback_clock.log 2>&1 $TAG"
SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
trap '[ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null' EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
cron_off() { "$CRONTAB" -l 2>/dev/null | grep -v "$TAG" | "$CRONTAB" - ; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal/callback_clock.py)" = "$TON1" ] || stop "the kit's file is not the built one"
if [ "${1:-}" = "--undo" ]; then
  cron_off; [ -f "$N1" ] && mv -f "$N1" "$N1.undone_S796"
  "$CRONTAB" -l 2>/dev/null | grep -q "$TAG" && echo "!! the cron line is still there -- send a photo" || echo "UNDONE: the call-back clock is off (the file kept as $N1.undone_S796; its store $CC_STORE left as it is)"
  exit 0
fi
echo "[1/4] kit files: all match SUMS.md5"
if [ "$(m5 "$N1")" = "$TON1" ] && [ "$("$CRONTAB" -l 2>/dev/null | grep -c "$TAG")" = 1 ]; then echo "-- ALREADY INSTALLED. Nothing written."; exit 0; fi
[ -e "$N1" ] && [ "$(m5 "$N1")" != "$TON1" ] && stop "$N1 is there and is not this kit's"
"$VPY" -B -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$KDIR/portal/callback_clock.py" 2>/dev/null || stop "the file does not compile with $VPY"
SCR=$(mktemp -d /tmp/s796.XXXX); chmod 700 "$SCR"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s796.py" "$KDIR" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" "$VPY" -W ignore -B "$KDIR/walk_s796.py" "$KDIR" 2>&1 | grep -E '^BAD|Error' | head -6); stop "the walk is not green ($R)";; esac
mkdir -p "$SCR/none/portal"
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s796.py" "$SCR/none" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control without the file did not go red ($R2)";; esac
[ -f "$CC_CONSOLE_DB" ] || stop "the Call Console's store is not at $CC_CONSOLE_DB"
D=$(cd "$SCR" && timeout 60 "$VPY" -B "$KDIR/portal/callback_clock.py" --dry 2>&1 | tail -1)
case "$D" in DRY*|*"is stale"*) ;; *) stop "the dry read of the live call store did not answer as expected ($D)";; esac
( cd "$SCR" && RING_PORTAL_DIR="$ROOT/portal" "$VPY" -B -c "import sys; sys.path.insert(0, '$ROOT/portal'); import ring_common as rc; assert callable(rc.push_user)" 2>/dev/null ) || stop "the portal's own push (ring_common.push_user) could not be loaded with $VPY"
echo "[2/4] the walk: $R | without the file: $R2 | the live call store now: $D"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
\cp "$KDIR/portal/callback_clock.py" "$N1.s796new" && mv -f "$N1.s796new" "$N1" || stop "could not place $N1"
[ "$(m5 "$N1")" = "$TON1" ] || { rm -f "$N1"; stop "the read-back did not match (removed again)"; }
"$CRONTAB" -l > "$ROOT/portal/crontab.bak_S796" 2>/dev/null
{ "$CRONTAB" -l 2>/dev/null | grep -v "$TAG"; echo "$LINE"; } | "$CRONTAB" - || { mv -f "$N1" "$N1.undone_S796"; stop "the cron line could not be added (the file taken back out)"; }
[ "$("$CRONTAB" -l 2>/dev/null | grep -c "$TAG")" = 1 ] || { cron_off; mv -f "$N1" "$N1.undone_S796"; stop "the cron line is not there (taken back out)"; }
echo "[3/4] placed $N1 (${TON1:0:8}); one cron line, every 5 minutes 08:00-21:55 IST (crontab kept in $ROOT/portal/crontab.bak_S796)"
echo "[4/4] $KIT: DONE. A missed caller not spoken to in 30 duty minutes is notified again to Shivani, Alisha and the reception mobile; at 60 to Shavez; the count still open at closing comes to you."
