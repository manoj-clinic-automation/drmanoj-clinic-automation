#!/usr/bin/env bash
# =============================================================================
#  install_S242_AMIR_TILE.sh
#
#  KIT   S242_AMIR_TILE -- Amir's own page gets a door, and it is the ONLY door
#        he carries.
#  RUN   bash /root/deploy/vps_deploy.sh S242_AMIR_TILE
#
#  TWO FILES, and they must move together -- a grant matches a tile by NAME, so
#  a new grant with no tile shows nothing and a new tile with no grant reaches
#  nobody but the doctor:
#    /root/portal/portal.py         ed558b3663c3dd100a24f58aafc32363
#                                -> d08721f69bc7c3e3a79a50192b20affb
#    /root/portal/tile_grants.json  710f13bd14ebfdf8108372c81414db1e  (v11)
#                                -> 7e7445a37ace9ea7c8218d598a05b81d  (v12)
#
#  NOTHING IS DELETED. The five tiles parked for Amir stay in portal.py with
#  their roles unchanged and are untouched for everybody else.
#  Red path restores BOTH files and restarts.
# =============================================================================
set -u

KIT="S242_AMIR_TILE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PORTAL_PY:-/root/wa/venv/bin/python3}"
P="${PORTAL_PATH:-/root/portal/portal.py}"
G="${TILE_GRANTS:-/root/portal/tile_grants.json}"
SVC="${PORTAL_SVC:-clinic-portal}"
PORT="${PORTAL_PORT:-8099}"
PB="ed558b3663c3dd100a24f58aafc32363"; PN="d08721f69bc7c3e3a79a50192b20affb"
GB="710f13bd14ebfdf8108372c81414db1e"; GN="7e7445a37ace9ea7c8218d598a05b81d"

PBAK=""; GBAK=""; APPLIED=0
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }

red() {
  if [ "$APPLIED" = "1" ]; then
    [ -n "$PBAK" ] && [ -f "$PBAK" ] && { \cp -p "$PBAK" "$P"; echo "   portal.py restored from $PBAK"; }
    [ -n "$GBAK" ] && [ -f "$GBAK" ] && { \cp -p "$GBAK" "$G"; echo "   tile_grants.json restored from $GBAK"; }
    systemctl restart "$SVC" >/dev/null 2>&1
    sleep 2
    echo "   portal.py is now $(md5of "$P") and the service is back up"
  fi
  echo "!! RED -- $*"
  exit 1
}

cd "$KDIR" || red "cannot enter the kit folder"

# -- gates, all from INSIDE this folder --------------------------------------
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(md5of tile_grants.json)" = "$GN" ] || red "the kit's tile_grants.json is not $GN"

[ -x "$PY" ] || red "$PY is not there"
[ -f "$P" ]  || red "$P is not there"
[ -f "$G" ]  || red "$G is not there"

PC="$(md5of "$P")"; GC="$(md5of "$G")"
if [ "$PC" = "$PN" ] && [ "$GC" = "$GN" ]; then
  echo "ALREADY INSTALLED -- portal.py $PN and tile_grants.json v12; nothing to do"
  exit 0
fi
[ "$PC" = "$PB" ] || red "portal.py is $PC, expected $PB. The box is not where this kit was built against -- read the pin and stop."
[ "$GC" = "$GB" ] || red "tile_grants.json is $GC, expected the v11 $GB. Install S242_DOCTERZ_COLLECTION_TILE first, or read the file."
echo "-- gates green; portal.py $PB and tile_grants.json v11"

# -- the walk, on THIS box, against a COPY, before anything real is touched ---
W="$(mktemp -d)"
\cp -p "$P" "$W/portal.py"
\cp -p tile_grants.json "$W/tile_grants.json"
\cp -p patch_portal_amir_tile_s242.py walk_amir_tile_s242.py "$W"/
( cd "$W" && "$PY" -B patch_portal_amir_tile_s242.py ./portal.py "$PB" ) || { rm -rf "$W"; red "the patcher refused on a copy of this box's portal.py -- nothing was changed"; }
[ "$(md5of "$W/portal.py")" = "$PN" ] || { rm -rf "$W"; red "patching a copy did not produce $PN -- nothing was changed"; }
( cd "$W" && "$PY" -B walk_amir_tile_s242.py ) || { rm -rf "$W"; red "the tile walk failed on this box -- nothing was changed"; }
rm -rf "$W"
echo "-- walked on this box: the patch reproduces $PN and every tile check passed"

# -- apply, for real ---------------------------------------------------------
STAMP="$(date +%Y%m%d_%H%M%S)"
PBAK="$P.bak_${KIT}_$STAMP"; GBAK="$G.bak_${KIT}_$STAMP"
\cp -p "$P" "$PBAK"; \cp -p "$G" "$GBAK"
APPLIED=1
OUT="$("$PY" -B patch_portal_amir_tile_s242.py "$P" "$PB" 2>&1)" || { echo "$OUT" | sed 's/^/   /'; red "the patcher refused on the real file"; }
echo "$OUT" | sed 's/^/   /'
[ "$(md5of "$P")" = "$PN" ] || red "portal.py is $(md5of "$P"), not $PN"
\cp -p tile_grants.json "$G"
[ "$(md5of "$G")" = "$GN" ] || red "tile_grants.json did not land as $GN"
"$PY" -m py_compile "$P" || red "py_compile portal.py"
rm -rf "$(dirname "$P")/__pycache__" 2>/dev/null

systemctl restart "$SVC" || red "the service would not restart"
sleep 3
systemctl is-active --quiet "$SVC" || red "the service is not active after the restart"
H="$(curl -s -o /dev/null -m 6 -w '%{http_code}' "http://127.0.0.1:$PORT/portal/health")"
L="$(curl -s -o /dev/null -m 6 -w '%{http_code}' "http://127.0.0.1:$PORT/portal/login")"
echo "-- health $H · login page $L"
[ "$H" = "200" ] && [ "$L" = "200" ] || red "health $H / login $L -- expected 200 and 200"

APPLIED=2
echo ""
echo "PINS  portal.py        $(md5of "$P")   was $PB"
echo "PINS  tile_grants.json $(md5of "$G")   was $GB  (v11 -> v12)"
echo "      backups $PBAK"
echo "              $GBAK"
echo "$KIT GREEN -- Amir now carries one tile, and it opens:"
echo "https://followup.dr-manoj.in/finance/amir"
echo "  Reverse:  \\cp -p $PBAK $P && \\cp -p $GBAK $G && systemctl restart $SVC"
