#!/bin/bash
# =============================================================================
#  install_b2c.sh · kit S202_B2C — a stale heartbeat is not a live watcher.
#
#  THE FAULT, IN CODE I SHIPPED THIS MORNING (B2A):
#    the watcher check read `alive` straight out of the payload and reported
#    "ok". But `alive` comes from a heartbeat FILE, and when the medical PC is
#    switched off overnight that file simply stops changing -- still saying
#    ALIVE, for ever. So the check showed a GREEN LIGHT FOR A MACHINE THAT WAS
#    OFF. A false green is worse than a false red, and it is the born-dead shape
#    the never-fired witness in that very kit exists to catch.
#
#  FIXED
#    * the heartbeat's AGE now gates it: stale -> "last heard N hours ago,
#      state unknown", never "ok". Threshold: pipeline.heartbeat_stale_hours (2).
#    * a new `medical` check for the pull failing to reach the PC, and it is
#      HOURS-AWARE: bad during clinic hours, info outside them. Alarming all
#      night about a PC that is meant to be off is how a light stops being read.
#      Settings: pipeline.clinic_hour_from (9) / pipeline.clinic_hour_to (21).
#
#  PROVEN OFFLINE: SMOKE 713 -> 719, +6 exactly, fail set byte-identical (48).
#  The six new checks assert the stale case, the fresh case, the explicitly-dead
#  case, and the in-hours / out-of-hours split.
# =============================================================================
set -u
KIT_NAME="S202_B2C"; APP=/root/finance/finance_app.py
APP_MD5_EXPECTED=3576c013464be4fc89eb850d3b5f8ab9
APP_MD5_NEW=50ac4c86a3985bf82269d650d5e46f0f
PY=/usr/bin/python3; SVC=clinic-finance.service
echo "=============================================================="
echo "  $KIT_NAME — a stale heartbeat is not a live watcher"
echo "=============================================================="
for c in md5sum awk cp date systemctl; do command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing"; exit 1; }; done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable"; exit 1; }
echo "[1/6] preflight ok"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/6] kit SUMS mismatch"; exit 1; }
echo "[2/6] kit integrity ok"
A="$(md5sum "$APP"|awk '{print $1}')"
[ "$A" = "$APP_MD5_EXPECTED" ] || { echo "!! [3/6] currency gate — $APP is $A, expected $APP_MD5_EXPECTED"; exit 1; }
echo "[3/6] currency gate ok"
BAK="${APP}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)"; cp -f "$APP" "$BAK" || { echo "!! backup failed"; exit 1; }
echo "[4/6] backup: $BAK"
restore(){ cp -f "$BAK" "$APP"; systemctl restart "$SVC" >/dev/null 2>&1; echo "   restored"; }
cp -f finance_app.py "$APP" || { restore; exit 1; }
[ "$(md5sum "$APP"|awk '{print $1}')" = "$APP_MD5_NEW" ] || { echo "!! installed bytes wrong"; restore; exit 1; }
systemctl restart "$SVC" || { restore; exit 1; }; sleep 2
systemctl is-active --quiet "$SVC" || { echo "!! service not active"; restore; exit 1; }
echo "[5/6] installed and $SVC active"
OUT="$(cd /root/finance && "$PY" finance_app.py --selftest 2>&1)"; SUM="$(echo "$OUT"|head -1)"
echo "      $SUM"
echo "$SUM" | grep -qE "(^|[^0-9])719/719([^0-9]|$)" || { echo "!! not 719/719 — restoring"; echo "$OUT"|grep FAIL|head -12; restore; exit 1; }
echo "[6/6] smoke 719/719 ✓  (was 713/713)"
echo
echo "  GREEN.  https://followup.dr-manoj.in/finance/health"
echo "  Overnight the watcher row will now read 'last heard N hours ago —"
echo "  state unknown' instead of a green 'alive'. That is the fix."
echo "  Reverse: cp -f $BAK $APP && systemctl restart $SVC"
