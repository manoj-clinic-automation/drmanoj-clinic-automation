#!/bin/bash
# install_S243_WATCHDOG_FINANCE.sh -- adds clinic-finance / staff-register / assetapp
# to the VPS watchdog's guarded-unit list. Full-file replacement of
# $ROOT/wa/clinic_watchdog.py, pinned from -> to by md5. Rolls back on any failure.
#
# One line to run on the VPS:
#   bash /root/deploy/repo/deploy_kits/S243_WATCHDOG_FINANCE/install_S243_WATCHDOG_FINANCE.sh
#
# No service restart is needed: clinic-watchdog.timer starts the script fresh
# every 5 minutes, so the next tick already runs the new file.
#
# Env (test only): ROOT=/some/dir (default /root)   FORCE_FAIL=1 forces the smoke to fail
set -e
set -u

ROOT="${ROOT:-/root}"
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$ROOT/wa/clinic_watchdog.py"
NEWFILE="$KIT_DIR/clinic_watchdog.py"

FROM_MD5="01ca6591a74ec8009bf9748fb7f480c2"
TO_MD5="00567d696b391f38f4f15499a0ade02e"
FROM8="${FROM_MD5:0:8}"
BAK="$TARGET.bak_S243_$FROM8"

PY="$ROOT/wa/venv/bin/python3"
if [ ! -x "$PY" ]; then PY="/usr/bin/python3"; fi
if [ ! -x "$PY" ]; then PY="$(command -v python3)"; fi

md5of() { md5sum "$1" | awk '{print $1}'; }

echo "== S243_WATCHDOG_FINANCE installer =="
echo "target : $TARGET"
echo "python : $PY"
echo "from   : $FROM_MD5"
echo "to     : $TO_MD5"

[ -f "$TARGET" ] || { echo "REFUSED: $TARGET not found"; exit 1; }
LIVE_MD5="$(md5of "$TARGET")"
echo "live   : $LIVE_MD5"

if [ "$LIVE_MD5" = "$TO_MD5" ]; then
  echo "ALREADY INSTALLED (live md5 == to-pin). Nothing to do."
  echo "md5sum of installed file:"; md5sum "$TARGET"
  exit 0
fi
if [ "$LIVE_MD5" != "$FROM_MD5" ]; then
  echo "REFUSED: live md5 is neither the from-pin nor the to-pin. Not touching the file."
  exit 1
fi

[ -f "$NEWFILE" ] || { echo "REFUSED: kit file missing: $NEWFILE"; exit 1; }
KIT_MD5="$(md5of "$NEWFILE")"
if [ "$KIT_MD5" != "$TO_MD5" ]; then
  echo "REFUSED: kit clinic_watchdog.py md5 $KIT_MD5 != expected $TO_MD5"; exit 1
fi

# stage .new and verify it byte-for-byte
cp "$NEWFILE" "$TARGET.new"
NEW_MD5="$(md5of "$TARGET.new")"
if [ "$NEW_MD5" != "$TO_MD5" ]; then
  echo "REFUSED: staged .new md5 $NEW_MD5 != $TO_MD5"; rm -f "$TARGET.new"; exit 1
fi
chmod --reference="$TARGET" "$TARGET.new" 2>/dev/null || chmod 755 "$TARGET.new"

# backup live (byte-identical) and verify the backup
cp -p "$TARGET" "$BAK"
[ "$(md5of "$BAK")" = "$FROM_MD5" ] || { echo "REFUSED: backup md5 mismatch"; rm -f "$TARGET.new"; exit 1; }
echo "backup : $BAK"

rollback() {
  echo "!! FAILURE -- restoring live file from $BAK"
  cp -p "$BAK" "$TARGET"
  R="$(md5of "$TARGET")"
  if [ "$R" = "$FROM_MD5" ]; then
    echo "ROLLED BACK OK: live md5 $R == from-pin (byte-identical restore)"
  else
    echo "ROLLBACK VERIFY FAILED: live md5 $R (expected $FROM_MD5) -- restore by hand from $BAK"
  fi
  rm -f "$TARGET.new"
  exit 1
}

mv "$TARGET.new" "$TARGET"
echo "installed -> $TARGET"

# smoke 1: py_compile with the venv python
if ! "$PY" -m py_compile "$TARGET"; then
  echo "smoke: py_compile FAILED"; rollback
fi
rm -rf "$ROOT/wa/__pycache__/clinic_watchdog."*.pyc 2>/dev/null || true
echo "smoke: py_compile OK"

# smoke 2: the watchdog has no dry/check mode (a real run touches systemctl
# and may push an alert), so the smoke is an import-only load that reads the
# SERVICES list and asserts 14 units incl. the 3 new ones. No network, no systemctl.
SMOKE_OUT="$("$PY" - "$TARGET" <<'PYEOF'
import sys, importlib.util, os
p = sys.argv[1]
spec = importlib.util.spec_from_file_location("clinic_watchdog_s243_smoke", p)
m = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode = True
spec.loader.exec_module(m)
units = [s[0] for s in m.SERVICES]
assert len(units) == 14, "expected 14 units, got %d" % len(units)
for u in ("clinic-finance.service", "staff-register.service", "assetapp.service"):
    assert units.count(u) == 1, u
print("SMOKE_OK units=%d" % len(units))
PYEOF
)" || { echo "smoke: import check FAILED"; rollback; }
echo "smoke: $SMOKE_OUT"
if [ "${FORCE_FAIL:-0}" = "1" ]; then
  echo "smoke: FORCE_FAIL=1 set (test hook) -- treating smoke as failed"; rollback
fi

FINAL="$(md5of "$TARGET")"
[ "$FINAL" = "$TO_MD5" ] || { echo "post-install md5 $FINAL != $TO_MD5"; rollback; }

echo "predicted post-install md5: $TO_MD5"
echo "md5sum of installed file:"; md5sum "$TARGET"
echo "No service restart needed: clinic-watchdog.timer runs the script fresh every 5 min."
echo "Rollback line: cp -p $BAK $TARGET"
echo "S243_WATCHDOG_FINANCE: DONE"
exit 0
