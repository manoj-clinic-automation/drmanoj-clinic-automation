#!/bin/bash
# =============================================================================
#  install_S615_BACKUP_THREE_GAPS.sh · kit S615 (session S336, 22-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S615_BACKUP_THREE_GAPS/install_S615_BACKUP_THREE_GAPS.sh
#  DRY=1 before bash: pins, rebuild, walk and control only -- nothing changed.   --undo: the S476 file back.
#
#  THE GAP (AF-19, S608, F-972): /root/wa/wa_logs/ (every incoming WhatsApp push), /root/wa/wa_inbox/send_log.jsonl
#  (every WhatsApp send) and /root/att_config.py (the attendance settings, secrets included) were in NO backup.
#  Two exact edits add them to the ENCRYPTED nightly (/root/state_backup/clinic_state_backup.py, cron 01:50).
#  No service to restart. After placing, the backup's own `preflight` proves every source, the encryption round
#  trip and Drive -- without shipping anything; if it fails, the old file goes back.
# =============================================================================
set -u
KIT="S615_BACKUP_THREE_GAPS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s615_backup}"
F="${F:-/root/state_backup/clinic_state_backup.py}"
PIN_IN="be57fe75f04b8b9020fcfd465b733578"
BOXFLAG="${BOXFLAG---box}"
W=/tmp/s615_walk
HAVE_LOCK=0
on_exit() { rm -rf "$W" /tmp/s615_rb.py /tmp/s615_pyc; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s615_pyc "$PY" -m py_compile clinic_state_backup.py walk_s615.py edits_s615.py || stop "the kit's code does not compile"
NEW=$(m5 clinic_state_backup.py)

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  b=$(ls -1t "$BK"/clinic_state_backup.py.bak_S615_* 2>/dev/null | head -1)
  [ -n "$b" ] && \cp -f "$b" "$F" && echo "    clinic_state_backup.py put back ($(m5 "$F" | cut -c1-8))"
  echo "UNDONE."; exit 0
fi

echo "[1] pins"
NOW=$(m5 "$F")
if [ "$NOW" = "$NEW" ]; then echo "    ALREADY INSTALLED (clinic_state_backup.py ${NEW:0:8})"; exit 0; fi
[ "$NOW" = "$PIN_IN" ] || stop "clinic_state_backup.py is not the S476 file this kit was built on (${NOW:0:8}, expected ${PIN_IN:0:8})"
echo "    clinic_state_backup.py ${NOW:0:8} (S476)"

echo "[2] rebuild from the live bytes"
"$PY" -B edits_s615.py "$F" /tmp/s615_rb.py "$KDIR/clinic_state_backup.py" || stop "the kit's file is not exactly the live file plus this kit's edits"

echo "[3] the walk (made-up files; then the three real paths, for size only) and the control"
rm -rf "$W"; mkdir -p "$W"; chmod 700 "$W"; \cp -f "$F" "$W/orig.py"
( cd "$W" && "$PY" -B "$KDIR/walk_s615.py" "$W/orig.py" "$KDIR/clinic_state_backup.py" $BOXFLAG > "$W/walk.txt" 2>&1 )
WK=$?; grep -E "on this machine" "$W/walk.txt" | sed 's/^ *ok */    /'; tail -1 "$W/walk.txt" | sed 's/^/    walk: /'
[ "$WK" = 0 ] || { grep "FAIL\|RED\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
( cd "$W" && "$PY" -B "$KDIR/walk_s615.py" "$W/orig.py" "$W/orig.py" > "$W/ctl.txt" 2>&1 )
[ $? != 0 ] && echo "    control on the live file: RED, as it must be" || stop "the control did not go red -- the walk cannot tell old from new"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[4] backup -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"
\cp -fp "$F" "$BK/clinic_state_backup.py.bak_S615_$NOW"; chmod 600 "$BK"/*
echo "    clinic_state_backup.py kept"

echo "[5] placed"
\cp -f clinic_state_backup.py "$F"
[ "$(m5 "$F")" = "$NEW" ] || { \cp -fp "$BK/clinic_state_backup.py.bak_S615_$NOW" "$F"; stop "the file did not land byte-exact" "The old file was put back."; }
echo "    clinic_state_backup.py ${NOW:0:8} -> ${NEW:0:8}"

echo "[6] the backup's own preflight (every source, the encryption round trip, Drive -- nothing shipped)"
timeout 900 "$PY" "$F" preflight > "$W/pre.txt" 2>&1
PF=$?
grep -E "would include|WARNING: source not present|FATAL|round trip|last success" "$W/pre.txt" | sed 's/^\[[^]]*\] /    /' | head -8
if [ "$PF" != 0 ]; then
  \cp -fp "$BK/clinic_state_backup.py.bak_S615_$NOW" "$F"
  stop "the backup's preflight did not pass (exit $PF)" "The old file was put back; tonight's backup runs as before."
fi
grep -q "source not present: /root/att_config.py\|source not present: /root/wa/" "$W/pre.txt" && {
  \cp -fp "$BK/clinic_state_backup.py.bak_S615_$NOW" "$F"
  stop "the preflight did not find one of the three" "The old file was put back."; }
echo "    preflight passed"

echo "[7] what this means for you"
echo "    From tonight (01:50), the WhatsApp logs, the WhatsApp send log and the attendance settings are in the"
echo "    encrypted nightly backup on Drive, like the call console and the staff ledger. Nothing on any page changes."
echo "[8] pins"
echo "    $(md5sum "$F")"
echo "DONE."
