#!/bin/bash
# =============================================================================
#  install_S719_GMB_STORE_BACKUP.sh . kit S719 (06-Nov-2026, session S390, the parent) . F-1129
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s719kit && cp -rp /root/deploy/repo/deploy_kits/S719_GMB_STORE_BACKUP /tmp/s719kit && bash /tmp/s719kit/install_S719_GMB_STORE_BACKUP.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s719kit/install_S719_GMB_STORE_BACKUP.sh --undo
#
#  THE GAP (F-1129, S389): /root/portal/gmb_store.db -- the GMB Review Assist store (S713, S717): every press, its drafts, the
#  Shared taps and the fortnightly readings -- is in NO backup. ONE source line adds it to the ENCRYPTED nightly
#  (/root/state_backup/clinic_state_backup.py, cron 01:50), through the sqlite online backup and the integrity check like the
#  other stores. No service to restart. After placing, the backup's own `preflight` proves every source, the encryption round
#  trip and Drive -- without shipping anything; if it fails, the old file goes back.
# =============================================================================
set -u
KIT="S719_GMB_STORE_BACKUP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s719_backup}"
F="${F:-/root/state_backup/clinic_state_backup.py}"
STORE="${STORE:-/root/portal/gmb_store.db}"
FROM=facfb8976578acd94a090a15daad9e12; TO=37ed5524ca4dffa96a19346bf6d3a012
WALK_OK="WALK OK 13/13"
W=""; HAVE_LOCK=0
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
on_exit() { [ -n "$W" ] && rm -rf "$W"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 clinic_state_backup.py)" = "$TO" ] || stop "the kit's clinic_state_backup.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  b=$(ls -1t "$BK"/clinic_state_backup.py.bak_S719_* 2>/dev/null | head -1)
  [ -n "$b" ] || stop "no S719 backup in $BK -- nothing to undo"
  \cp -f "$b" "$F" && echo "UNDONE: clinic_state_backup.py put back ($(m5 "$F" | cut -c1-8))"; exit 0
fi
echo "1. kit files: all match SUMS.md5"
NOW=$(m5 "$F")
if [ "$NOW" = "$TO" ]; then echo "-- ALREADY INSTALLED (clinic_state_backup.py ${TO:0:8})"; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "clinic_state_backup.py is not the file this kit was built on (${NOW:0:8}, expected ${FROM:0:8})"
echo "2. the live clinic_state_backup.py is ${FROM:0:8} (S661)"
[ -f "$STORE" ] || stop "$STORE is not on the box -- adding it would refuse the whole night (FATAL 41)"
"$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); sys.exit(0 if c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' else 1)" "$STORE" \
  || stop "the GMB store does not pass its own integrity check -- the night would refuse to ship"
echo "3. the GMB store is there and passes its integrity check ($(du -k "$STORE" | cut -f1) KB)"
W=$(mktemp -d /tmp/s719w.XXXX); chmod 700 "$W"; \cp -f "$F" "$W/live.py"
R=$(cd "$W" && "$PY" -B "$KDIR/walk_s719.py" "$W/live.py" "$KDIR/clinic_state_backup.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$W" && "$PY" -B "$KDIR/walk_s719.py" "$W/live.py" "$KDIR/clinic_state_backup.py" 2>&1 | grep FAIL | head); stop "the walk is not green ($R)"; }
echo "4. the walk (made-up files: the live file + one line; a WAL store copied whole): $R"
R=$(cd "$W" && "$PY" -B "$KDIR/walk_s719.py" "$W/live.py" "$W/live.py" 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control (the live file in the kit's place): $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$F")" = "$FROM" ] || stop "clinic_state_backup.py changed while this kit was checking -- run the line again"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -fp "$F" "$BK/clinic_state_backup.py.bak_S719_$NOW"; chmod 600 "$BK"/*
echo "5. backup: $BK/clinic_state_backup.py.bak_S719_${NOW:0:8}"
\cp -f clinic_state_backup.py "$F"
[ "$(m5 "$F")" = "$TO" ] || { \cp -fp "$BK/clinic_state_backup.py.bak_S719_$NOW" "$F"; stop "the file did not land byte-exact" "The old file was put back."; }
echo "6. placed clinic_state_backup.py ${FROM:0:8} -> ${TO:0:8}"
echo "7. the backup's own preflight (every source, the encryption round trip, Drive -- nothing shipped)"
timeout 900 "$PY" "$F" preflight > "$W/pre.txt" 2>&1
PF=$?
grep -E "would include|WARNING: source not present|FATAL|round trip|last success" "$W/pre.txt" | sed 's/^\[[^]]*\] /    /' | head -8
if [ "$PF" != 0 ]; then
  \cp -fp "$BK/clinic_state_backup.py.bak_S719_$NOW" "$F"
  stop "the backup's preflight did not pass (exit $PF)" "The old file was put back; tonight's backup runs as before."
fi
grep -q "skipping gmb_store.db" "$W/pre.txt" && { \cp -fp "$BK/clinic_state_backup.py.bak_S719_$NOW" "$F"; stop "the preflight skips the GMB store as over the size guard" "The old file was put back."; }
grep -q "source not present: $STORE" "$W/pre.txt" && { \cp -fp "$BK/clinic_state_backup.py.bak_S719_$NOW" "$F"; stop "the preflight did not find the GMB store" "The old file was put back."; }
echo "   preflight passed"
echo ""
echo "$KIT: DONE. From tonight (01:50) the GMB Review Assist store is in the encrypted nightly backup on Drive. Nothing on any page changes."
