#!/bin/bash
# ===========================================================================
# S196_ATT1 — Staff self-service (My biometric + mark-me-present) and
#             machine late-minutes in the day grid.
#   staff_register.py   v0.2 -> v0.3   (cef76859... -> c2059ea1...)
#   att_month_report.py v2.5 -> v2.6   (e64cad19... -> 9ab98313...)
# D317-style chained install: every gate passes BEFORE anything moves;
# any failure after the move restores the backups and restarts the service.
# Run:  bash deploy_kits/S196_ATT1/INSTALL_S196_ATT1.sh
# ===========================================================================
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"          # path-agnostic (F-141 lesson)
PY=/root/wa/venv/bin/python3
SR=/root/staff_register/staff_register.py
AR=/root/att_month_report.py

# pins — transcribed from md5sum runs on the built files (F-109/F-116: a hash
# is transcribed from a file or it is not written)
OLD_SR="cef768594bee5360a388e66028456495"
OLD_AR="e64cad19d135618dec1413553e6bdc80"
NEW_SR="c2059ea1e0157da6cbf820502f4925a3"
NEW_AR="9ab98313bbda7ae5555fb4b5a5a82c4b"

MOVED=0
fail() {
  echo ""
  echo "❌ FAILED at: $1"
  if [ "$MOVED" = "1" ]; then
    echo "   Restoring backups..."
    [ -f "$SR.bak_S196" ] && cp "$SR.bak_S196" "$SR"
    [ -f "$AR.bak_S196" ] && cp "$AR.bak_S196" "$AR"
    systemctl restart staff-register
    echo "   Backups restored, staff-register restarted. Nothing half-installed."
  else
    echo "   Nothing was moved. The live files are untouched."
  fi
  exit 1
}

md5of() { md5sum "$1" | awk '{print $1}'; }

echo "[1/9] Currency gate — the live files must be the exact pinned versions"
[ "$(md5of $SR)" = "$OLD_SR" ] || fail "live staff_register.py is $(md5of $SR), expected $OLD_SR (repo/Register out of date — STOP, reconcile first)"
[ "$(md5of $AR)" = "$OLD_AR" ] || fail "live att_month_report.py is $(md5of $AR), expected $OLD_AR (STOP, reconcile first)"
echo "      OK — both live files match their pins."

echo "[2/9] Payload gate — the kit files must be the exact built bytes"
[ "$(md5of "$KIT/staff_register.py.new")" = "$NEW_SR" ] || fail "kit staff_register.py.new corrupted in transit"
[ "$(md5of "$KIT/att_month_report.py.new")" = "$NEW_AR" ] || fail "kit att_month_report.py.new corrupted in transit"
echo "      OK — payloads intact."

echo "[3/9] Backups"
cp "$SR" "$SR.bak_S196" || fail "backup staff_register"
cp "$AR" "$AR.bak_S196" || fail "backup att_month_report"
echo "      OK — .bak_S196 beside each file."

echo "[4/9] Install (.new beside target -> md5 in place -> mv) — F-66 order"
cp "$KIT/staff_register.py.new" "$SR.new"      || fail "copy staff_register.py.new"
cp "$KIT/att_month_report.py.new" "$AR.new"    || fail "copy att_month_report.py.new"
[ "$(md5of $SR.new)" = "$NEW_SR" ] || fail "in-place md5 staff_register.py.new"
[ "$(md5of $AR.new)" = "$NEW_AR" ] || fail "in-place md5 att_month_report.py.new"
mv "$SR.new" "$SR"; mv "$AR.new" "$AR"
MOVED=1
echo "      OK — files in position."

echo "[5/9] Compile with the VPS venv (F-53)"
$PY -m py_compile "$SR" || fail "py_compile staff_register.py"
$PY -m py_compile "$AR" || fail "py_compile att_month_report.py"
echo "      OK."

echo "[6/9] Register --init (adds present_request table + staff.username +"
echo "      daily_register.late_minutes — additive, non-destructive)"
$PY "$SR" --init || fail "staff_register --init"

echo "[7/9] Username mapping (login -> staff row; names only, no salaries)"
$PY "$SR" --map-usernames || fail "staff_register --map-usernames"

echo "[8/9] Selftests (throwaway stores; live data untouched)"
$PY "$SR" --selftest || fail "staff_register --selftest"
$PY "$AR" --selftest || fail "att_month_report --selftest"
echo "      OK — both suites green."

echo "[9/9] Restart staff-register + health"
systemctl restart staff-register || fail "systemctl restart staff-register"
sleep 2
systemctl is-active --quiet staff-register || fail "staff-register not active after restart"
curl -s -o /dev/null -w "      /register/health -> HTTP %{http_code}\n" -m 5 http://127.0.0.1:8044/register/health
echo ""
echo "✅ S196_ATT1 INSTALLED."
echo "   staff_register.py  $NEW_SR  (v0.3)"
echo "   att_month_report.py $NEW_AR (v2.6)"
echo "   Pins moved — regenerate live_pins.txt at the close (A8/F-134)."
echo "   No other service touched; attendance core untouched (frozen, D251)."
