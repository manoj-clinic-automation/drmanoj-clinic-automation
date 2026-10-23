#!/bin/bash
# install_s634.sh -- S634_PROCROOM_LIST (D773 Kit 1; board _numbers v631 -> v632; built in the Scan App chat, session 345, 23-Oct-2026).
#   The procedure-room goods, Kit 1: the owner's product list (the new part procroom.py, his page "Procedure room" in the one menu);
#   on the sorting desk, a Procedure room paper's lines each get a product, quantity, brand and PLACE (Procedure room, Home use, Clinic
#   equipment, OT, Sanjeevni -- orthotics flagged); NO rate on the desk; his rates, his slips from photos, his allowances on his page.
#   sorting_desk.py (10 counted edits), asset_register.py (2), NEW procroom.py. assets.db ADDITIVE: three new tables (proc_item,
#   proc_slip, proc_line), made by the part's own ensure() at mount; the data step writes his list of 30 products once.
#   Restarts assetapp only.
# BUILD_NORM_v1 s3 order: gates -> the build lock -> pins (TO = ALREADY INSTALLED; else FROM, procroom.py absent; the read-only files)
# -> rebuild from the live bytes (make_s634.py) -> the TO pins -> compile -> the walk on the REAL app (every part, a COPY of the live
# database, made-up rows) on the TO files + the control on the live FROM files (must be red) -- DRY=1 stops here -> backups beside the
# files and of the database -> place -> md5 read-back -> restart assetapp -> /healthz 200, /procroom 302, the new door answers a
# logged-out POST with 302, no part NOT mounted in the log -> the data step (the list, once) -> what the pages now show -> undo line.
# A failure after placing puts the files back byte-identically (procroom.py moved aside) and restarts.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S634_PROCROOM_LIST/install_s634.sh
set -u
KIT="S634_PROCROOM_LIST"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S634_APP_DIR:-/root/assetapp}"
SERVICE="${S634_SERVICE:-assetapp}"
HEALTH="${S634_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S634_PYTHON:-python3}"
RESTART="${S634_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S634_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S634_HOST:-srv1746119}"
REH="${S634_REHEARSAL:-}"
if [ -z "${S634_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S634_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S634_HEALTH_TRIES:-20}"
FILES="sorting_desk.py asset_register.py"
NEW="procroom.py"
READONLY="clinic_papers.py asset_machine.py stationery.py batteries.py xray_costs.py claude_reader.py claude_reread.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES $NEW; do rm -f "$APP/$f.s634tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S634_FAKE_HEALTH:-}" ]; then echo "$S634_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s634.py walk_s634_app.py procroom.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for f in $FILES; do for k in PIN_FROM_$(base $f).txt PIN_TO_$(base $f).txt; do v="$(pin $k)"; [ ${#v} -eq 32 ] || die "$k is missing in the kit"; done; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
v="$(pin PIN_TO_procroom.txt)"; [ ${#v} -eq 32 ] || die "PIN_TO_procroom.txt is missing in the kit"
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
[ -f "$APP/$NEW" ] && [ "$(md5 "$APP/$NEW")" = "$(pin PIN_TO_procroom.txt)" ] || ALL_TO=0
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (sorting_desk.py, asset_register.py and procroom.py at the kit's TO pins)"
  for f in $FILES $NEW; do echo "  PIN $f $(md5 "$APP/$f")"; done
  exit 0
fi
for f in $FILES; do L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S634 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
[ -e "$APP/$NEW" ] && die "$APP/$NEW is already there ($(md5 "$APP/$NEW" | cut -c1-8)), not at the TO pin -- stop and re-check"
echo "    procroom.py absent, as it must be before this kit"
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s634work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "rebuild from the live bytes (counted edits), the new part, and the TO pins"
"$PY" -B "$HERE/make_s634.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"; done
[ "$(md5 "$WORK/to/$NEW")" = "$(pin PIN_TO_procroom.txt)" ] || die "the new procroom.py is not at its TO pin"
for f in $FILES $NEW; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    the TO files = their pins and compile"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s634_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s634_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { cat "$WORK/capp.txt"; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "backups beside the live files, and of the database"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S634_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S634_${P:0:8}"; done
STAMP="$(date '+%Y%m%d_%H%M%S')"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S634_$STAMP" || die "the database backup failed"
echo "    $(basename "$DB").bak_S634_$STAMP"

restore(){
  echo "RESTORING sorting_desk.py and asset_register.py from their backups; procroom.py moved aside"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S634_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ -e "$APP/$NEW" ] && mv -f "$APP/$NEW" "$APP/$NEW.off_S634"
  [ -e "$APP/$NEW" ] && RB=1
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S634_ copies beside them are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S634_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (through temporary files) and read back"
cp -p "$WORK/to/$NEW" "$APP/$NEW.s634tmp" && mv -f "$APP/$NEW.s634tmp" "$APP/$NEW" || restore
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s634tmp" && mv -f "$APP/$f.s634tmp" "$APP/$f" || restore; done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done
[ "$(md5 "$APP/$NEW")" = "$(pin PIN_TO_procroom.txt)" ] || restore; echo "    $NEW $(md5 "$APP/$NEW" | cut -c1-8) = the TO pin (new)"

log "restart $SERVICE only, then its health, the page and the new door"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S634_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/procroom")"; [ -n "${S634_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S634_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /procroom answered ${X:-nothing}, not 302"; restore; }
echo "    /procroom 302 (the login door: the page is mounted)"
if [ -z "$REH" ]; then
  PR="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST "${HEALTH%/healthz}/procroom/slip" 2>/dev/null || true)"
  [ "$PR" = "302" ] || { echo "    the new door /procroom/slip answered ${PR:-nothing}, not 302 -- it did not mount"; restore; }
  echo "    the new door /procroom/slip answers 302 to a logged-out POST (mounted; writes nothing)"
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

log "the data step: the owner's list, once (procroom.py --seed)"
"$PY" -B "$APP/$NEW" --seed "$DB" | sed 's/^/    /'
[ "${PIPESTATUS[0]}" = 0 ] || echo "    !! the data step did not finish -- the page works; the list can be typed on it, or this line run again"
echo
echo "WHAT THE PAGES NOW SHOW:"
echo "  - the one menu (yours only): 'Procedure room' -- https://followup.dr-manoj.in/scanapp/procroom"
echo "    worth a look; by product (bought, spent, last rate and brand); by month for the financial year; lines kept elsewhere;"
echo "    every slip with its rates to type; + a slip from a photo; rarely used and retired; your list (30 products) and the gloves allowance;"
echo "  - the sorting desk (you and Shavez): with 'Procedure room' chosen, a box 'Procedure room lines' -- each line's product,"
echo "    quantity, brand and place (Procedure room, Home use, Clinic equipment, OT, Sanjeevni); no rupee and no rate on it."
echo "UNDO (puts the two files back, moves procroom.py aside and restarts the scan app; the new tables stay, unread):"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S634_${P:0:8} $APP/$f"; done
echo "  mv -f $APP/$NEW $APP/$NEW.off_S634"
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
