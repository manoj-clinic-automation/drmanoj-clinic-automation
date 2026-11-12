#!/bin/bash
# =============================================================================
#  install_S806_WA_STORES_BACKUP.sh . kit S806 (12-Nov-2026, session S439, the parent) . D939 (the WhatsApp items, d)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s806kit && cp -rp /root/deploy/repo/deploy_kits/S806_WA_STORES_BACKUP /tmp/s806kit && bash /tmp/s806kit/install_S806_WA_STORES_BACKUP.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s806kit/install_S806_WA_STORES_BACKUP.sh --undo
#
#  THE GAP: /root/portal/wa_ladder.db (S798: the WhatsApp STOP list and the listener's place) and /root/portal/callback_clock.db
#  (S796: the call-back clock's store) are in NO backup. TWO source lines add them to the ENCRYPTED nightly
#  (/root/state_backup/clinic_state_backup.py, cron 01:50), through the sqlite online backup and the integrity check like the
#  other stores. No service to restart. After placing, the backup's own `preflight` proves every source, the encryption round
#  trip and Drive -- without shipping anything; if it fails, the old file goes back. S719's pattern.
# =============================================================================
set -u
KIT="S806_WA_STORES_BACKUP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s806_backup}"
F="${F:-/root/state_backup/clinic_state_backup.py}"
STORE1="${STORE1:-/root/portal/wa_ladder.db}"
STORE2="${STORE2:-/root/portal/callback_clock.db}"
FROM=fd1647de19a20e908baa3d1f958ad07d; TO=5282b72c7a552e578f570a7df9d74385
WALK_OK="WALK OK 17/17"
W=""; HAVE_LOCK=0
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
on_exit() { [ -n "$W" ] && rm -rf "$W"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
back() { \cp -fp "$BK/clinic_state_backup.py.bak_S806_$NOW" "$F"; [ "$(m5 "$F")" = "$FROM" ] || echo "   !! THE OLD FILE DID NOT GO BACK -- copy $BK/clinic_state_backup.py.bak_S806_$NOW over $F by hand"; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 clinic_state_backup.py)" = "$TO" ] || stop "the kit's clinic_state_backup.py is not the built one"
if [ "${1:-}" = "--undo" ]; then
  b=$(ls -1t "$BK"/clinic_state_backup.py.bak_S806_* 2>/dev/null | head -1)
  [ -n "$b" ] || stop "no S806 backup in $BK -- nothing to undo"
  L=$(m5 "$F"); { [ "$L" = "$TO" ] || [ "$L" = "$FROM" ]; } || stop "clinic_state_backup.py has been changed since this kit (a later kit is on top) -- not undone"
  [ "$(m5 "$b")" = "$FROM" ] || stop "the S806 backup in $BK is not the file this kit replaced -- not undone"
  \cp -f "$b" "$F"; [ "$(m5 "$F")" = "$FROM" ] && { echo "UNDONE: clinic_state_backup.py put back ($(m5 "$F" | cut -c1-8))"; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
echo "1. kit files: all match SUMS.md5"
NOW=$(m5 "$F")
if [ "$NOW" = "$TO" ]; then echo "-- ALREADY INSTALLED (clinic_state_backup.py ${TO:0:8})"; exit 0; fi
[ "$NOW" = "$FROM" ] || stop "clinic_state_backup.py is not the file this kit was built on (${NOW:0:8}, expected ${FROM:0:8})"
echo "2. the live clinic_state_backup.py is ${FROM:0:8} (S747)"
for S in "$STORE1" "$STORE2"; do
  [ -f "$S" ] || stop "$S is not on the box -- adding it would refuse the whole night (FATAL 41)"
  "$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); sys.exit(0 if c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' else 1)" "$S" \
    || stop "$(basename "$S") does not pass its own integrity check -- the night would refuse to ship"
done
echo "3. both stores are there and pass their integrity check ($(basename "$STORE1") $(du -k "$STORE1" | cut -f1) KB, $(basename "$STORE2") $(du -k "$STORE2" | cut -f1) KB)"
W=$(mktemp -d /tmp/s806w.XXXX) || stop "no scratch folder could be made in /tmp"
[ -n "$W" ] && [ -d "$W" ] || stop "no scratch folder could be made in /tmp"
chmod 700 "$W"; \cp -f "$F" "$W/live.py"
R=$(cd "$W" && TMPDIR="$W" "$PY" -B "$KDIR/walk_s806.py" "$W/live.py" "$KDIR/clinic_state_backup.py" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$W" && TMPDIR="$W" "$PY" -B "$KDIR/walk_s806.py" "$W/live.py" "$KDIR/clinic_state_backup.py" 2>&1 | grep FAIL | head); stop "the walk is not green ($R)"; }
echo "4. the walk (made-up files: the live file + two lines; two WAL stores and a store being written, copied sound): $R"
R=$(cd "$W" && TMPDIR="$W" "$PY" -B "$KDIR/walk_s806.py" "$W/live.py" "$W/live.py" 2>&1 | tail -1)
case "$R" in "WALK RED"*) echo "   control (the live file in the kit's place): $R -- red, as it must be";; *) stop "the control did not go red ($R)";; esac
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$F")" = "$FROM" ] || stop "clinic_state_backup.py changed while this kit was checking -- run the line again"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -fp "$F" "$BK/clinic_state_backup.py.bak_S806_$NOW" && [ "$(m5 "$BK/clinic_state_backup.py.bak_S806_$NOW")" = "$FROM" ] || stop "could not keep a backup of clinic_state_backup.py"
chmod 600 "$BK"/*
echo "5. backup: $BK/clinic_state_backup.py.bak_S806_${NOW:0:8}"
\cp -f clinic_state_backup.py "$F"
[ "$(m5 "$F")" = "$TO" ] || { back; stop "the file did not land byte-exact" "The old file was put back."; }
echo "6. placed clinic_state_backup.py ${FROM:0:8} -> ${TO:0:8}"
echo "7. the backup's own preflight (every source, the encryption round trip, Drive -- nothing shipped)"
timeout 900 "$PY" "$F" preflight > "$W/pre.txt" 2>&1
PF=$?
grep -E "would include|WARNING: source not present|FATAL|round trip|last success" "$W/pre.txt" | sed 's/^\[[^]]*\] /    /' | head -8
if [ "$PF" != 0 ]; then
  back
  stop "the backup's preflight did not pass (exit $PF)" "The old file was put back ($(m5 "$F" | cut -c1-8)); tonight's backup runs as before."
fi
for S in "$STORE1" "$STORE2"; do
  grep -q "skipping $(basename "$S")" "$W/pre.txt" && { back; stop "the preflight skips $(basename "$S") as over the size guard" "The old file was put back."; }
  grep -q "source not present: $S" "$W/pre.txt" && { back; stop "the preflight did not find $S" "The old file was put back."; }
  grep -q "database: $(basename "$S") integrity_check -> ok" "$W/pre.txt" || { back; stop "the preflight does not show $(basename "$S") taken and sound" "The old file was put back."; }
done
echo "   preflight passed"
echo ""
echo "$KIT: DONE. From tonight (01:50) the WhatsApp stop list's store and the call-back clock's store are in the encrypted nightly backup on Drive. Nothing on any page changes."
