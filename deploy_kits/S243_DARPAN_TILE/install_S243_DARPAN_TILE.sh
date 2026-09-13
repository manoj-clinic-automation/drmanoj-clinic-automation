#!/bin/bash
# =============================================================================
#  install_S243_DARPAN_TILE.sh -- kit S243_DARPAN_TILE -- "Kal ka hisaab": Darpan's day gets its
#  door (owner's ruling 13-Sep-2026: his day now lives at /finance/darpan/kal; his tile must open it).
#
#  Run by:  bash /root/deploy/repo/deploy_kits/S243_DARPAN_TILE/install_S243_DARPAN_TILE.sh
#
#  PORTAL ONLY (clinic-portal.service).  The finance app is not touched.
#  A  portal.py          patched ON THIS BOX by patch_portal_darpan_tile_s243.py on a COPY, then
#                        placed: the tile "Kal ka hisaab" -> /finance/darpan/kal, roles [doctor],
#                        immediately before Daily Sale, plus its group row.  Two anchors, each
#                        exactly once, else REFUSED and nothing changes.  Nothing removed or moved.
#  B  tile_grants.json   v13 -> v14 (the kit's full file): granted by name to darpan.  Corrections
#                        was never in his grants (checked; the walk proves he is not shown it), so
#                        the CA ruling costs no line here.  Every other login is byte-equal to v13.
#
#  Pins this kit was built on (the live state after S243_REPORTS_TILE):
#      portal.py           4bb6bde0e2e07033ac0e0f5d7a7daaf6 -> 06f1b378608fbc97c54bc1f546d7985c
#      tile_grants.json    c9ee95c39bb805086b79d95327b2b626 (v13) -> 0efad736e71de7199e7c596a5b3d0c2e (v14)
#
#  Gates: SUMS + KIT_ID -> live pins (both, exact) -> patch on a copy, must hash to the to-pin
#  -> py_compile -> .bak_S243_<pin8> of both files -> place -> import smoke (the portal's own
#  grouping assert; the tile present; grants v14; darpan shown it; the doctor still shown
#  Corrections) -> ONLY THEN restart clinic-portal -> /portal/health 200 within 20 s.
#  Any RED after placing: both files restored, the service restarted only if this run restarted
#  it, exit 1.  Re-run when already installed: ALREADY INSTALLED.
#
#  ROOT=<dir> prefixes every absolute path (mock test only).  MOCK_PORTAL_PIN / MOCK_GRANTS_PIN /
#  MOCK_SMOKE_FAIL / PY exist for the same mock and print loudly when used.
#
#  AFTER INSTALL: nothing is left for the owner.  Darpan opens the portal, taps "Kal ka hisaab".
# =============================================================================
set -e
set -u
set -o pipefail
KIT="S243_DARPAN_TILE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"
PORTAL_DIR="$ROOT/root/portal"
PF="$PORTAL_DIR/portal.py"
GF="$PORTAL_DIR/tile_grants.json"
SVC_POR="clinic-portal.service"
HZ_POR="http://127.0.0.1:8099/portal/health"

PORTAL_FROM_PIN="${MOCK_PORTAL_PIN:-4bb6bde0e2e07033ac0e0f5d7a7daaf6}"
PORTAL_TO_PIN="06f1b378608fbc97c54bc1f546d7985c"
GRANTS_FROM_PIN="${MOCK_GRANTS_PIN:-c9ee95c39bb805086b79d95327b2b626}"
GRANTS_TO_PIN="0efad736e71de7199e7c596a5b3d0c2e"
PORTAL_MARK='"name": "Kal ka hisaab"'

if [ -z "${PY:-}" ]; then
  if [ -x "$ROOT/root/wa/venv/bin/python3" ]; then PY="$ROOT/root/wa/venv/bin/python3"; else PY="/usr/bin/python3"; fi
fi
if [ -n "$ROOT" ]; then echo "-- MOCK: ROOT=$ROOT PY=$PY"; fi
for v in MOCK_PORTAL_PIN MOCK_GRANTS_PIN MOCK_SMOKE_FAIL; do
  if [ -n "${!v:-}" ]; then echo "-- MOCK: $v override ${!v}"; fi
done

P_BAK=""; G_BAK=""
PLACED_P=0; PLACED_G=0; RESTARTED_POR=0
m5() { md5sum "$1" | awk '{print $1}'; }

rollback() {
  if [ "$PLACED_P" -eq 1 ] && [ -n "$P_BAK" ] && [ -f "$P_BAK" ]; then
    \cp -f "$P_BAK" "$PF" && echo "   restored portal.py from $P_BAK ($(m5 "$PF" | cut -c1-8))"
  fi
  if [ "$PLACED_G" -eq 1 ] && [ -n "$G_BAK" ] && [ -f "$G_BAK" ]; then
    \cp -f "$G_BAK" "$GF" && echo "   restored tile_grants.json from $G_BAK ($(m5 "$GF" | cut -c1-8))"
  fi
  rm -rf "$PORTAL_DIR/__pycache__" 2>/dev/null || true
  if [ "$RESTARTED_POR" -eq 1 ]; then
    systemctl restart "$SVC_POR" || true; sleep 3
    if systemctl is-active --quiet "$SVC_POR"; then echo "   $SVC_POR back up on the restored files"; else echo "   !! $SVC_POR did not come back after the restore -- check: systemctl status $SVC_POR"; fi
  fi
}
red() { echo "!! RED -- $*"; rollback; echo "!! $KIT NOT installed"; exit 1; }
trap 'red "unexpected error at line $LINENO"' ERR

cd "$KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed -- the kit folder is not what was published"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(m5 "$KDIR/tile_grants.json")" = "$GRANTS_TO_PIN" ] || red "the kit's tile_grants.json is not $GRANTS_TO_PIN"
echo "-- gates green: SUMS.md5 and KIT_ID.txt ($KIT); grants v14 $GRANTS_TO_PIN"

for f in "$PF" "$GF"; do [ -f "$f" ] || red "$f is absent"; done
LIVE_P="$(m5 "$PF")"; LIVE_G="$(m5 "$GF")"
P_DONE=0; G_DONE=0
grep -qF "$PORTAL_MARK" "$PF" && P_DONE=1
[ "$LIVE_G" = "$GRANTS_TO_PIN" ] && G_DONE=1
if [ "$P_DONE" -eq 1 ] && [ "$G_DONE" -eq 1 ]; then
  echo "-- ALREADY INSTALLED: portal.py ${LIVE_P:0:8} carries the Kal ka hisaab tile; tile_grants.json is v14 ${LIVE_G:0:8}. Nothing changed."
  exit 0
fi
if [ "$P_DONE" -eq 0 ]; then
  [ "$LIVE_P" = "$PORTAL_FROM_PIN" ] || red "live portal.py is ${LIVE_P} -- not the pin ${PORTAL_FROM_PIN:0:8} this kit was built on (the state after S243_REPORTS_TILE); NOTHING changed"
fi
if [ "$G_DONE" -eq 0 ]; then
  [ "$LIVE_G" = "$GRANTS_FROM_PIN" ] || red "live tile_grants.json is ${LIVE_G} -- not the v13 ${GRANTS_FROM_PIN:0:8} this kit was built on; NOTHING changed"
fi
echo "-- live pins: portal.py ${LIVE_P:0:8} | tile_grants.json ${LIVE_G:0:8} (as expected)"

# ---- the patch on a COPY, before anything is placed; the anchor count is the real guard
W="$(mktemp -d)"
if [ "$P_DONE" -eq 0 ]; then
  \cp -f "$PF" "$W/portal.py"
  ( cd "$W" && "$PY" -B "$KDIR/patch_portal_darpan_tile_s243.py" ./portal.py "$LIVE_P" >/dev/null ) || { rm -rf "$W"; red "the portal patcher refused on a copy of this box's portal.py -- NOTHING changed"; }
  [ "$(m5 "$W/portal.py")" = "$PORTAL_TO_PIN" ] || { rm -rf "$W"; red "patching a copy of portal.py did not produce $PORTAL_TO_PIN -- NOTHING changed"; }
  grep -qF "$PORTAL_MARK" "$W/portal.py" || { rm -rf "$W"; red "the patched copy does not carry the tile"; }
  "$PY" -m py_compile "$W/portal.py" || { rm -rf "$W"; red "py_compile of the patched portal.py copy"; }
  rm -rf "$W/__pycache__" 2>/dev/null || true
fi
echo "-- prepared: portal.py copy $([ "$P_DONE" -eq 0 ] && echo "${PORTAL_TO_PIN:0:8}" || echo '(already)') | py_compile clean with $PY"

# ---- backups, then place
if [ "$P_DONE" -eq 0 ]; then
  P_BAK="$PF.bak_S243_${LIVE_P:0:8}"; \cp -f "$PF" "$P_BAK"
  \cp -f "$W/portal.py" "$PF"; PLACED_P=1
  [ "$(m5 "$PF")" = "$PORTAL_TO_PIN" ] || red "portal.py did not land as $PORTAL_TO_PIN"
fi
rm -rf "$W"
if [ "$G_DONE" -eq 0 ]; then
  G_BAK="$GF.bak_S243_${LIVE_G:0:8}"; \cp -f "$GF" "$G_BAK"
  \cp -f "$KDIR/tile_grants.json" "$GF"; PLACED_G=1
  [ "$(m5 "$GF")" = "$GRANTS_TO_PIN" ] || red "tile_grants.json did not land as $GRANTS_TO_PIN"
fi
rm -rf "$PORTAL_DIR/__pycache__" 2>/dev/null || true
echo "-- placed: portal.py ${LIVE_P:0:8} -> $(m5 "$PF" | cut -c1-8) | tile_grants.json ${LIVE_G:0:8} -> $(m5 "$GF" | cut -c1-8) | backups .bak_S243_<pin8>"

# ---- import smoke BEFORE any restart: the tile exists and is grouped (portal's own assert), the
#      grants file is v14, darpan is shown it, the doctor is still shown Corrections
SMOKE_RC=0
if [ -n "${MOCK_SMOKE_FAIL:-}" ]; then
  SMOKE_OUT="MOCK_SMOKE_FAIL set -- pretending the import failed"; SMOKE_RC=1
else
  SMOKE_OUT="$(cd "$PORTAL_DIR" && TILE_GRANTS_FILE="$GF" PORTAL_PIN_SALT="${PORTAL_PIN_SALT:-smoke}" PORTAL_TOKEN_SEED="${PORTAL_TOKEN_SEED:-smoke}" "$PY" -B -c "
import portal
assert any(t['name']=='Kal ka hisaab' and t['url']=='/finance/darpan/kal' for t in portal.TILES), 'tile absent'
g=portal._tile_grants(); assert g and g.get('version')==14, 'grants not v14'
vis=lambda role,user: [t['name'] for _g,items in portal._visible_sections(role, False, user) for t in items]
d=vis('staff','darpan'); assert 'Kal ka hisaab' in d, 'darpan not shown the tile'; assert 'Corrections' not in d, 'darpan shown Corrections'
m=vis('doctor','manoj'); assert 'Kal ka hisaab' in m and 'Corrections' in m and 'Daily Sale' in m, 'the doctor lost a tile'
print('import ok: tile present, grants v14, darpan sees it, no Corrections for him, the doctor keeps everything')" 2>&1)" || SMOKE_RC=$?
fi
rm -rf "$PORTAL_DIR/__pycache__" 2>/dev/null || true
[ "$SMOKE_RC" -eq 0 ] || red "portal import smoke failed -- the service was NOT restarted:
$(echo "$SMOKE_OUT" | tail -8)"
echo "-- smoke portal: $(echo "$SMOKE_OUT" | tail -1)"

# ---- restart and prove
RESTARTED_POR=1
systemctl restart "$SVC_POR" || red "systemctl restart $SVC_POR failed"
HZ=""; j=0
while [ $j -lt 20 ]; do
  HZ="$(curl -s -o /dev/null -w '%{http_code}' "$HZ_POR" 2>/dev/null || true)"
  if [ "$HZ" = "200" ]; then break; fi
  sleep 1; j=$((j+1))
done
[ "$HZ" = "200" ] || red "portal health answered '$HZ' after 20 s"
systemctl is-active --quiet "$SVC_POR" || red "$SVC_POR is not active"
echo "-- portal health 200 after ${j}s"
RESTARTED_POR=2
echo ""
echo "== $KIT INSTALLED"
echo "   portal.py                  was ${LIVE_P}  actual $(m5 "$PF")"
echo "   tile_grants.json           was ${LIVE_G}  actual $(m5 "$GF")  (v13 -> v14)"
echo "   backups: $P_BAK  $G_BAK  (rollback line in README)"
echo "   Darpan's tile: Kal ka hisaab -> https://followup.dr-manoj.in/finance/darpan/kal"
exit 0
