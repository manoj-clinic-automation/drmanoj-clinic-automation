#!/bin/bash
# mock_install_darpan_tile_s243.sh -- the installer's proofs on a throw-away ROOT.  Nothing live is touched.
#   1 refuses a wrong portal.py pin (nothing placed)       2 refuses a wrong grants pin (nothing placed)
#   3 installs on the true pins: predicted to-pins, two .bak_S243_<pin8>, smoke green, ONE restart
#   4 second run says ALREADY INSTALLED                    5 health failure -> both files restored, restart on the restored files
#   6 import smoke failure -> both files restored and the service is NEVER restarted
# Needs the live-shape portal.py (4bb6bde0) and the v13 grants (c9ee95c3):
#   PORTAL_SRC=<dir holding portal.py 4bb6bde0 and tile_grants.json c9ee95c3> bash mock_install_darpan_tile_s243.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
PORTAL_SRC="${PORTAL_SRC:-/root/portal}"
P=0; F=0
chk() { if [ "$2" -eq 0 ]; then P=$((P+1)); echo "  PASS  $1"; else F=$((F+1)); echo "  FAIL  $1"; fi; }

build_root() {   # $1 = root dir
  local M="$1"
  mkdir -p "$M/root/portal" "$M/bin"
  cp "$PORTAL_SRC/portal.py" "$PORTAL_SRC/tile_grants.json" "$M/root/portal/"
  cat > "$M/bin/systemctl" <<'EOF'
#!/bin/bash
echo "[mock systemctl] $*" >&2
exit 0
EOF
  cat > "$M/bin/curl" <<'EOF'
#!/bin/bash
if [ -n "${MOCK_HZ_FAIL:-}" ]; then printf '000'; else printf '200'; fi
EOF
  chmod +x "$M/bin/systemctl" "$M/bin/curl"
}

M="$(mktemp -d /tmp/mock_dtile_XXXXXX)"
build_root "$M"
export PATH="$M/bin:$PATH"
P0="$(md5sum "$M/root/portal/portal.py" | cut -c1-32)"
G0="$(md5sum "$M/root/portal/tile_grants.json" | cut -c1-32)"
echo "== mock root $M  portal $P0  grants $G0"
[ "$P0" = "4bb6bde0e2e07033ac0e0f5d7a7daaf6" ] && [ "$G0" = "c9ee95c39bb805086b79d95327b2b626" ]; chk "the mock starts from the live pins (4bb6bde0 / c9ee95c3)" $?
unchanged() { [ "$(md5sum "$1/root/portal/portal.py" | cut -c1-32)" = "$P0" ] && [ "$(md5sum "$1/root/portal/tile_grants.json" | cut -c1-32)" = "$G0" ] \
  && [ ! -f "$1/root/portal/portal.py.bak_S243_${P0:0:8}" ] && [ ! -f "$1/root/portal/tile_grants.json.bak_S243_${G0:0:8}" ]; }

echo "---- proof 1: wrong portal.py pin is refused"
ROOT="$M" PY=python3 MOCK_PORTAL_PIN=00000000000000000000000000000000 bash "$KDIR/install_S243_DARPAN_TILE.sh" > "$M/p1.log" 2>&1; rc=$?
grep -q "live portal.py is" "$M/p1.log" && [ $rc -ne 0 ] && unchanged "$M" && ! grep -q "mock systemctl" "$M/p1.log"; chk "refused, nothing placed, no restart" $?

echo "---- proof 2: wrong grants pin is refused"
ROOT="$M" PY=python3 MOCK_GRANTS_PIN=00000000000000000000000000000000 bash "$KDIR/install_S243_DARPAN_TILE.sh" > "$M/p2.log" 2>&1; rc=$?
grep -q "live tile_grants.json is" "$M/p2.log" && [ $rc -ne 0 ] && unchanged "$M" && ! grep -q "mock systemctl" "$M/p2.log"; chk "refused, nothing placed, no restart" $?

echo "---- proof 3: install on the true pins"
ROOT="$M" PY=python3 bash "$KDIR/install_S243_DARPAN_TILE.sh" > "$M/p3.log" 2>&1; rc=$?
[ $rc -eq 0 ] && grep -q "== S243_DARPAN_TILE INSTALLED" "$M/p3.log"; chk "installer exit 0, INSTALLED" $?
[ "$(md5sum "$M/root/portal/portal.py" | cut -c1-32)" = "06f1b378608fbc97c54bc1f546d7985c" ]; chk "portal.py landed as the predicted pin 06f1b378" $?
[ "$(md5sum "$M/root/portal/tile_grants.json" | cut -c1-32)" = "0efad736e71de7199e7c596a5b3d0c2e" ]; chk "tile_grants.json landed as v14 0efad736" $?
[ -f "$M/root/portal/portal.py.bak_S243_${P0:0:8}" ] && [ -f "$M/root/portal/tile_grants.json.bak_S243_${G0:0:8}" ] \
  && [ "$(md5sum "$M/root/portal/portal.py.bak_S243_${P0:0:8}" | cut -c1-32)" = "$P0" ]; chk "two .bak_S243_<pin8> backups holding the from-bytes" $?
grep -q "smoke portal: import ok: tile present, grants v14, darpan sees it" "$M/p3.log"; chk "import smoke green (darpan shown it, no Corrections, doctor keeps everything)" $?
[ "$(grep -c "mock systemctl\] restart clinic-portal" "$M/p3.log")" = "1" ]; chk "clinic-portal restarted exactly once, after the smoke" $?
grep -q "portal health 200" "$M/p3.log"; chk "health polled to 200" $?
[ ! -d "$M/root/portal/__pycache__" ]; chk "no __pycache__ left in the portal folder" $?

echo "---- proof 4: second run is ALREADY INSTALLED"
ROOT="$M" PY=python3 bash "$KDIR/install_S243_DARPAN_TILE.sh" > "$M/p4.log" 2>&1; rc=$?
[ $rc -eq 0 ] && grep -q "ALREADY INSTALLED" "$M/p4.log" && [ "$(md5sum "$M/root/portal/portal.py" | cut -c1-32)" = "06f1b378608fbc97c54bc1f546d7985c" ] \
  && ! grep -q "mock systemctl" "$M/p4.log"; chk "ALREADY INSTALLED, nothing moved, no restart" $?

echo "---- proof 5: health fails -> full rollback"
M5="$(mktemp -d /tmp/mock_dtile5_XXXXXX)"; build_root "$M5"
ROOT="$M5" PY=python3 MOCK_HZ_FAIL=1 bash "$KDIR/install_S243_DARPAN_TILE.sh" > "$M5/p5.log" 2>&1; rc=$?
[ $rc -ne 0 ] && grep -q "RED" "$M5/p5.log" && [ "$(md5sum "$M5/root/portal/portal.py" | cut -c1-32)" = "$P0" ] \
  && [ "$(md5sum "$M5/root/portal/tile_grants.json" | cut -c1-32)" = "$G0" ]; chk "RED, both files back to the from-pins" $?
grep -q "restored portal.py" "$M5/p5.log" && grep -q "restored tile_grants.json" "$M5/p5.log"; chk "rollback named what it restored" $?
[ "$(grep -c "mock systemctl\] restart clinic-portal" "$M5/p5.log")" = "2" ]; chk "service restarted again on the restored files" $?

echo "---- proof 6: import smoke fails -> rollback, and the service is NEVER restarted"
M6="$(mktemp -d /tmp/mock_dtile6_XXXXXX)"; build_root "$M6"
ROOT="$M6" PY=python3 MOCK_SMOKE_FAIL=1 bash "$KDIR/install_S243_DARPAN_TILE.sh" > "$M6/p6.log" 2>&1; rc=$?
[ $rc -ne 0 ] && grep -q "service was NOT restarted" "$M6/p6.log" && [ "$(md5sum "$M6/root/portal/portal.py" | cut -c1-32)" = "$P0" ] \
  && [ "$(md5sum "$M6/root/portal/tile_grants.json" | cut -c1-32)" = "$G0" ]; chk "RED before the restart, both files back" $?
! grep -q "mock systemctl\] restart" "$M6/p6.log"; chk "no restart at all" $?

echo ""
echo "MOCK INSTALL: $P passed, $F failed   (logs under $M, $M5, $M6)"
[ $F -eq 0 ]
