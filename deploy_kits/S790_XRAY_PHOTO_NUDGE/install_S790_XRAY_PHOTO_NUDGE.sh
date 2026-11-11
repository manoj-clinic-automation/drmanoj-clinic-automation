#!/bin/bash
# =============================================================================
#  install_S790_XRAY_PHOTO_NUDGE.sh . kit S790 (11-Nov-2026, session S428, the parent) . the owner 09:49 / 09:51 IST: a phone notification at
#  3 p.m. and 6 p.m. for X-ray photos not yet in the folder; done shown as done, not done stays flagged.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s790kit && cp -rp /root/deploy/repo/deploy_kits/S790_XRAY_PHOTO_NUDGE /tmp/s790kit && bash /tmp/s790kit/install_S790_XRAY_PHOTO_NUDGE.sh
#  NEW /root/finance/xray_photo_nudge.py + two cron lines (15:00, 18:00). No live file changed, no restart.
#  Undo:  bash /tmp/s790kit/install_S790_XRAY_PHOTO_NUDGE.sh --undo
# =============================================================================
set -u
KIT="S790_XRAY_PHOTO_NUDGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
CRONTAB="${CRONTAB:-crontab}"
N1="$ROOT/finance/xray_photo_nudge.py"; TON1=73d5a43f0d6bc8ee30046b71a7fb8e5d
DB="${FINANCE_DB:-$ROOT/finance/finance.db}"
L15="0 15 * * * $VPY -B $N1 >> $ROOT/finance/xray_photo_nudge.log 2>&1 # S790_XRAY_PHOTO_NUDGE"
L18="0 18 * * * $VPY -B $N1 >> $ROOT/finance/xray_photo_nudge.log 2>&1 # S790_XRAY_PHOTO_NUDGE"
SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
trap '[ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null' EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
cron_off() { "$CRONTAB" -l 2>/dev/null | grep -v '# S790_XRAY_PHOTO_NUDGE' | "$CRONTAB" - ; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 finance/xray_photo_nudge.py)" = "$TON1" ] || stop "the kit's file is not the built one"
if [ "${1:-}" = "--undo" ]; then
  cron_off; [ -f "$N1" ] && mv -f "$N1" "$N1.undone_S790"
  "$CRONTAB" -l 2>/dev/null | grep -q '# S790_XRAY_PHOTO_NUDGE' && echo "!! the cron lines are still there -- send a photo" || echo "UNDONE: the two notifications are off (the file kept as $N1.undone_S790)"
  exit 0
fi
echo "[1/4] kit files: all match SUMS.md5"
if [ "$(m5 "$N1")" = "$TON1" ] && [ "$("$CRONTAB" -l 2>/dev/null | grep -c '# S790_XRAY_PHOTO_NUDGE')" = 2 ]; then echo "-- ALREADY INSTALLED. Nothing written."; exit 0; fi
[ -e "$N1" ] && [ "$(m5 "$N1")" != "$TON1" ] && stop "$N1 is there and is not this kit's"
"$VPY" -W ignore -B -m py_compile "$KDIR/finance/xray_photo_nudge.py" 2>/dev/null || stop "the file does not compile with $VPY"
SCR=$(mktemp -d /tmp/s790.XXXX); chmod 700 "$SCR"
"$VPY" -c "import sqlite3; s=sqlite3.connect('file:$DB?mode=ro', uri=True); d=sqlite3.connect('$SCR/f.db'); s.backup(d); d.close(); s.close()" 2>/dev/null || stop "could not copy finance.db for the walk"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s790.py" "$KDIR" "$SCR/f.db" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" "$VPY" -W ignore -B "$KDIR/walk_s790.py" "$KDIR" "$SCR/f.db" 2>&1 | grep -E '^BAD|Error' | head -6); stop "the walk on a copy of today's database is not green ($R)";; esac
mkdir -p "$SCR/none/finance"
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s790.py" "$SCR/none" "$SCR/f.db" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control without the file did not go red ($R2)";; esac
rm -f "$SCR/f.db"
D=$(cd "$SCR" && FINANCE_DB="$DB" timeout 60 "$VPY" -B "$KDIR/finance/xray_photo_nudge.py" --dry 2>&1 | tail -1)
echo "[2/4] the walk (a copy of today's finance.db): $R | without the file: $R2 | now: $D"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
\cp "$KDIR/finance/xray_photo_nudge.py" "$N1.s790new" && mv -f "$N1.s790new" "$N1" || stop "could not place $N1"
[ "$(m5 "$N1")" = "$TON1" ] || { rm -f "$N1"; stop "the read-back did not match (removed again)"; }
"$CRONTAB" -l > "$ROOT/finance/crontab.bak_S790" 2>/dev/null
{ "$CRONTAB" -l 2>/dev/null | grep -v '# S790_XRAY_PHOTO_NUDGE'; echo "$L15"; echo "$L18"; } | "$CRONTAB" - || { mv -f "$N1" "$N1.undone_S790"; stop "the cron lines could not be added (the file taken back out)"; }
[ "$("$CRONTAB" -l 2>/dev/null | grep -c '# S790_XRAY_PHOTO_NUDGE')" = 2 ] || { cron_off; mv -f "$N1" "$N1.undone_S790"; stop "the cron lines are not both there (taken back out)"; }
echo "[3/4] placed $N1 (${TON1:0:8}); two cron lines at 15:00 and 18:00 IST (crontab kept in $ROOT/finance/crontab.bak_S790)"
echo "[4/4] $KIT: DONE. At 3 pm and 6 pm the staff phones (and yours) get the X-ray photo count -- or 'all in'."
