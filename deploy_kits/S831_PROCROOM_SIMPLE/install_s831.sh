#!/bin/bash
# install_s831.sh -- S831_PROCROOM_SIMPLE (board _numbers v1476 -> v1477; built in the Scan App chat, session 461, 14-Nov-2026; D982).
#   His Procedure room page simplified to the mock-up he called final (v4, 14:40 IST 14-Nov-2026): the tiles, Start here, Expenses and
#   revenue for the financial year (the X-ray page's way; each month: what was bought, and the procedures done one row per patient slip
#   with its fee and its items, editable -- saved through the morning screen's own save), Stock now with his count and reorder level
#   (gloves in whole pairs), the rest folded, a fixed Top. procroom.py rebuilt on the box from its FROM pin (S831's TO) by the kit's
#   counted edits and checked against the kit's whole file; no other file; no data step; restarts assetapp only. Staff screens unchanged.
#   Same order and gates as S831's installer.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S831_PROCROOM_SIMPLE/install_s831.sh
set -u
KIT="S831_PROCROOM_SIMPLE"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S831_APP_DIR:-/root/assetapp}"
SERVICE="${S831_SERVICE:-assetapp}"
HEALTH="${S831_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S831_PYTHON:-python3}"
RESTART="${S831_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S831_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S831_HOST:-srv1746119}"
REH="${S831_REHEARSAL:-}"
if [ -z "${S831_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S831_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S831_HEALTH_TRIES:-20}"
FILES="procroom.py"
READONLY="sorting_desk.py clinic_papers.py asset_register.py asset_machine.py stationery.py batteries.py xray_costs.py claude_reader.py claude_reread.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s831tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S831_FAKE_HEALTH:-}" ]; then echo "$S831_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s831.py edits_s831.py walk_s831_app.py procroom.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for f in $FILES; do for k in PIN_FROM_$(base $f).txt PIN_TO_$(base $f).txt; do v="$(pin $k)"; [ ${#v} -eq 32 ] || die "$k is missing in the kit"; done; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ "$(md5 "$HERE/procroom.py")" = "$(pin PIN_TO_procroom.txt)" ] || die "the kit's procroom.py is not at its pin"
for f in $READONLY; do v="$(pin PIN_READ_$(base $f).txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base $f).txt is missing in the kit"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    the kit and $APP ok"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (procroom.py at the kit's TO pin)"
  for f in $FILES; do echo "  PIN $f $(md5 "$APP/$f")"; done
  exit 0
fi
for f in $FILES; do L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S831 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s831work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "the kit's procroom.py on the pinned FROM bytes, and its TO pin"
"$PY" -B "$HERE/make_s831.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"; done
for f in $FILES; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    the TO files = their pins and compile"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s831_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s831_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { cat "$WORK/capp.txt"; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "backups beside the live files, and of the database"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S831_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S831_${P:0:8}"; done
STAMP="$(date '+%Y%m%d_%H%M%S')"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S831_$STAMP" || die "the database backup failed"
echo "    $(basename "$DB").bak_S831_$STAMP"

restore(){
  echo "RESTORING procroom.py from its backup"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S831_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S831_ copies beside them are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S831_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (through temporary files) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s831tmp" && mv -f "$APP/$f.s831tmp" "$APP/$f" || restore; done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health, the page and the new door"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S831_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/procroom")"; [ -n "${S831_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S831_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /procroom answered ${X:-nothing}, not 302"; restore; }
echo "    /procroom 302 (the login door: the page is mounted)"
if [ -z "$REH" ]; then
  PR="$(curl -s --max-time 10 "${HEALTH%/healthz}/procroom/morning/api/open" 2>/dev/null || true)"
  printf '%s' "$PR" | grep -q '"why": *"signed out"' || { echo "    the count door /procroom/morning/api/open answered '${PR:0:80}', not the signed-out JSON -- it did not mount"; restore; }
  printf '%s' "$PR" | grep -q '"open"' && { echo "    the count door gave a count to a signed-out call"; restore; }
  echo "    the count door /procroom/morning/api/open answers a signed-out call with ok:false and no open field (mounted; reads nothing)"
  U="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "${HEALTH%/healthz}/procroom/used" 2>/dev/null || true)"
  [ "$U" = "405" ] || { echo "    the month Save's door /procroom/used answered a GET with ${U:-nothing}, not 405 -- it did not mount"; restore; }
  echo "    the month Save's door /procroom/used is mounted (a GET is refused: 405)"
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

echo
echo "WHAT THE PAGES NOW SHOW:"
echo "  - Your Procedure room page (Scan app > Procedure room) is the simplified one you called final: six tiles at the top (spent, procedure"
echo "    revenue, procedures done, Fibrecast in stock today, waiting for you, the morning screen), each a link; Start here in three steps;"
echo "    Expenses and revenue for the financial year -- each month opens to what was bought and to every patient slip with a procedure,"
echo "    its fee and its items, which you can correct or fill and Save (your change replaces Shavez's entry; his stays in the record);"
echo "    Stock now with your count and the reorder level in one Save -- gloves in pairs, never a decimal; the rest folded at the foot."
echo "  - Yuvika's papers are called dealer challans on this page. Nothing changes on any staff screen."
echo "UNDO (puts procroom.py back and restarts the scan app; every count, reorder level and entry you saved stays):"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S831_${P:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
