#!/bin/bash
# =============================================================================
#  install_S610_ATT_DOUBLE_PRESS.sh · kit S610 (session S331, 21-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S610_ATT_DOUBLE_PRESS/install_S610_ATT_DOUBLE_PRESS.sh
#  DRY=1 before bash: pins, rebuild, walk and control only.   --undo at the end: the old file back.
#
#  THE OWNER, 21-Oct-2026 18:56 IST (Surendra's October attendance): "few days he has punched twice and is mentioned
#  out there wrongly".  A second press within 30 minutes of the first is a double press on arrival, not an OUT --
#  the salary sheet's own rule (att_month_report.ARTEFACT_WINDOW_MIN), now on https://attendance.dr-manoj.in too.
#  Display only: no attendance or salary figure changes.
# =============================================================================
set -u
KIT="S610_ATT_DOUBLE_PRESS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s610_backup}"
RD="${RD:-/root}"
SVC="${SVC:-attendance-dashboard}"
PIN_IN="ebd8bd85fa9734286fcb11766a5d1715"
W=/tmp/s610_walk
HAVE_LOCK=0
on_exit() { rm -rf "$W" /tmp/s610_rb.py; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s610_pyc "$PY" -m py_compile att_dashboard.py walk_s610.py edits_s610.py || stop "the kit's code does not compile"
rm -rf /tmp/s610_pyc
NEW=$(m5 att_dashboard.py)
PORT=$(cd "$RD" && "$PY" -B -c "import att_config as c; print(c.DASHBOARD_PORT)" 2>/dev/null)
[ -n "$PORT" ] || PORT=8044

check_up() {
  OKH=0
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  for i in $(seq 1 25); do
    sleep 1
    C=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/login")
    [ "$C" = "200" ] && break
  done
  [ "$C" = "200" ] && [ "$(systemctl is-active "$SVC")" = "active" ] && OKH=1
}

if [ "${1:-}" = "--undo" ]; then
  echo "[undo]"
  b=$(ls -1t "$BK"/att_dashboard.py.bak_S610_* 2>/dev/null | head -1)
  [ -n "$b" ] && \cp -f "$b" "$RD/att_dashboard.py" && echo "    att_dashboard.py put back ($(m5 "$RD/att_dashboard.py" | cut -c1-8))"
  systemctl restart "$SVC" </dev/null >/dev/null 2>&1; sleep 3
  echo "    $SVC: $(systemctl is-active "$SVC")"; echo "UNDONE."; exit 0
fi

echo "[1] pins"
NOW=$(m5 "$RD/att_dashboard.py")
if [ "$NOW" = "$NEW" ]; then echo "    ALREADY INSTALLED (att_dashboard.py ${NEW:0:8})"; exit 0; fi
[ "$NOW" = "$PIN_IN" ] || stop "att_dashboard.py is not the file this kit was built on (${NOW:0:8}, expected ${PIN_IN:0:8})"
echo "    att_dashboard.py ${NOW:0:8}"

echo "[2] rebuild from the live bytes"
"$PY" -B edits_s610.py "$RD/att_dashboard.py" /tmp/s610_rb.py "$KDIR/att_dashboard.py" || stop "the kit's file is not exactly the live file plus this kit's edits"

echo "[3] the walk (a made-up person and punches in a scratch folder; the live punches are not opened)"
rm -rf "$W"; mkdir -p "$W/new" "$W/old"; chmod 700 "$W"
\cp -f att_dashboard.py "$W/new/"; \cp -f "$RD/att_dashboard.py" "$W/old/"
( cd "$W" && "$PY" -B "$KDIR/walk_s610.py" --code "$W/new" --base "$RD" --scratch "$W/s1" > "$W/walk.txt" 2>&1 )
WK=$?; grep -E "^WALK" "$W/walk.txt" | sed 's/^/    /'
[ "$WK" = 0 ] || { grep "FAIL\|Error" "$W/walk.txt" | head -8; stop "the walk is not green"; }
( cd "$W" && "$PY" -B "$KDIR/walk_s610.py" --code "$W/old" --base "$RD" --scratch "$W/s2" > "$W/ctl.txt" 2>&1 )
[ $? != 0 ] && echo "    control on the live file: RED, as it must be" || stop "the control did not go red"
rm -rf "$W"
if [ "${DRY:-0}" = "1" ]; then echo "-- DRY RUN: nothing changed"; exit 0; fi

echo "[4] backup -> $BK"
mkdir -p "$BK"; chmod 700 "$BK"; \cp -f "$RD/att_dashboard.py" "$BK/att_dashboard.py.bak_S610_$NOW"; chmod 600 "$BK"/*

echo "[5] placed"
\cp -f att_dashboard.py "$RD/att_dashboard.py"
[ "$(m5 "$RD/att_dashboard.py")" = "$NEW" ] || stop "att_dashboard.py did not land byte-exact" "Run the line again with --undo at the end."
echo "    att_dashboard.py ${NOW:0:8} -> ${NEW:0:8}"

echo "[6] $SVC restarted and checked"
check_up
if [ "$OKH" != 1 ]; then
  \cp -f "$BK/att_dashboard.py.bak_S610_$NOW" "$RD/att_dashboard.py"; systemctl restart "$SVC" </dev/null >/dev/null 2>&1
  stop "the attendance page did not come back" "The old file was put back and $SVC restarted."
fi
echo "    the attendance page answers (login 200)"
echo "    $(md5sum "$RD/att_dashboard.py")"
echo "DONE. Open https://attendance.dr-manoj.in/month"
