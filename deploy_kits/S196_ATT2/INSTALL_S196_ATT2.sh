#!/bin/bash
# ===========================================================================
# S196_ATT2 — PWA install kit for the staff self page ("My Biometric").
#   staff_register.py v0.3 -> v0.4  (c2059ea1... -> 9087954c...)
# Adds: /register/manifest.webmanifest + the clinic-logo app icons (embedded),
# head links on /register/me ONLY. NO service worker, nothing cached offline,
# no schema change, no other page touched.
# Run:  bash deploy_kits/S196_ATT2/INSTALL_S196_ATT2.sh
# ===========================================================================
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
PY=/root/wa/venv/bin/python3
SR=/root/staff_register/staff_register.py

OLD_SR="c2059ea1e0157da6cbf820502f4925a3"   # v0.3, live since S196_ATT1
NEW_SR="9087954c8a4a891e8cdd848d6a9d48b2"   # v0.4

MOVED=0
fail() {
  echo ""
  echo "❌ FAILED at: $1"
  if [ "$MOVED" = "1" ]; then
    echo "   Restoring backup..."
    [ -f "$SR.bak_S196b" ] && cp "$SR.bak_S196b" "$SR"
    systemctl restart staff-register
    echo "   Backup restored, staff-register restarted. Nothing half-installed."
  else
    echo "   Nothing was moved. The live file is untouched."
  fi
  exit 1
}

md5of() { md5sum "$1" | awk '{print $1}'; }

echo "[1/6] Currency gate — live staff_register.py must be the S196_ATT1 pin"
[ "$(md5of $SR)" = "$OLD_SR" ] || fail "live file is $(md5of $SR), expected $OLD_SR (STOP, reconcile first)"
echo "      OK."

echo "[2/6] Payload gate"
[ "$(md5of "$KIT/staff_register.py.new")" = "$NEW_SR" ] || fail "kit payload corrupted in transit"
echo "      OK."

echo "[3/6] Backup + install (.new -> md5 in place -> mv, F-66 order)"
cp "$SR" "$SR.bak_S196b" || fail "backup"
cp "$KIT/staff_register.py.new" "$SR.new" || fail "copy"
[ "$(md5of $SR.new)" = "$NEW_SR" ] || fail "in-place md5"
mv "$SR.new" "$SR"
MOVED=1
echo "      OK — file in position."

echo "[4/6] Compile with the VPS venv (F-53)"
$PY -m py_compile "$SR" || fail "py_compile"
echo "      OK."

echo "[5/6] Selftest (throwaway stores; live data untouched)"
$PY "$SR" --selftest || fail "selftest"
echo "      OK."

echo "[6/6] Restart + health + live PWA routes"
systemctl restart staff-register || fail "restart"
sleep 2
systemctl is-active --quiet staff-register || fail "service not active"
curl -s -o /dev/null -w "      /register/health              -> HTTP %{http_code}\n" -m 5 http://127.0.0.1:8044/register/health
curl -s -o /dev/null -w "      /register/manifest.webmanifest -> HTTP %{http_code}\n" -m 5 http://127.0.0.1:8044/register/manifest.webmanifest
curl -s -o /dev/null -w "      /register/pwa-icon-192.png     -> HTTP %{http_code}\n" -m 5 http://127.0.0.1:8044/register/pwa-icon-192.png
echo ""
echo "✅ S196_ATT2 INSTALLED."
echo "   staff_register.py  $NEW_SR  (v0.4)"
echo "   Staff phones: open attendance.dr-manoj.in/register/me in Chrome,"
echo "   sign in, menu -> 'Add to Home screen' -> the clinic-logo app icon."
echo "   Pin moved again — live_pins.txt regen at the close covers both."
