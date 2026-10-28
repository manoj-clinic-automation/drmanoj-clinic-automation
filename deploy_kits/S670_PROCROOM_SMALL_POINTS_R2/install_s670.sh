#!/bin/bash
# install_s670.sh -- S670_PROCROOM_SMALL_POINTS_R2 (board _numbers v749 -> v750; built in the Scan App chat, session 355, 28-Oct-2026).
#   S656_PROCROOM_SMALL_POINTS again, byte-for-byte in procroom.py (e51c00a1, its 13 counted edits, VERSION S656): S656's install of
#   28-Oct stopped at its walk on the copy of the live database (F-1032: check N6 counted Shavez's real saved slips with its own) and
#   placed nothing. procroom.py, its edits and pins unchanged; the walk changes -- N6 counts its own made-up slips, and in its
#   SCRATCH copy only Shavez's saved slips and shelf counts are cleared first, S1 finds Fibrecast in Order now by name, N5 checks the
#   stockinette and injection lines by name -- and the kit's name. S656's folder is frozen (F-512).
#   What procroom.py does: proc_use.lkey added to a table made before it; ONE pre-match rule at the month end (a retired product only
#   where that scan holds it -- a slip sent twice never counted twice); typed rates kept across Its scan. No other file; no data step;
#   restarts assetapp only. Same order and gates as S648's installer.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S670_PROCROOM_SMALL_POINTS_R2/install_s670.sh
set -u
KIT="S670_PROCROOM_SMALL_POINTS_R2"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S670_APP_DIR:-/root/assetapp}"
SERVICE="${S670_SERVICE:-assetapp}"
HEALTH="${S670_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S670_PYTHON:-python3}"
RESTART="${S670_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S670_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S670_HOST:-srv1746119}"
REH="${S670_REHEARSAL:-}"
if [ -z "${S670_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S670_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S670_HEALTH_TRIES:-20}"
FILES="procroom.py"
READONLY="sorting_desk.py clinic_papers.py asset_register.py asset_machine.py stationery.py batteries.py xray_costs.py claude_reader.py claude_reread.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s670tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S670_FAKE_HEALTH:-}" ]; then echo "$S670_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s656.py edits_s656.py walk_s670_app.py procroom.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
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
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S670 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s670work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "the kit's procroom.py on the pinned FROM bytes, and its TO pin"
"$PY" -B "$HERE/make_s656.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"; done
for f in $FILES; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    the TO files = their pins and compile"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s670_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s670_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { cat "$WORK/capp.txt"; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "backups beside the live files, and of the database"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S670_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S670_${P:0:8}"; done
STAMP="$(date '+%Y%m%d_%H%M%S')"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S670_$STAMP" || die "the database backup failed"
echo "    $(basename "$DB").bak_S670_$STAMP"

restore(){
  echo "RESTORING procroom.py from its backup"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S670_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S670_ copies beside them are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S670_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (through temporary files) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s670tmp" && mv -f "$APP/$f.s670tmp" "$APP/$f" || restore; done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health, the page and the new door"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S670_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/procroom")"; [ -n "${S670_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S670_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /procroom answered ${X:-nothing}, not 302"; restore; }
echo "    /procroom 302 (the login door: the page is mounted)"
if [ -z "$REH" ]; then
  PR="$(curl -s --max-time 10 "${HEALTH%/healthz}/procroom/morning/api/open" 2>/dev/null || true)"
  printf '%s' "$PR" | grep -q '"why": *"signed out"' || { echo "    the new door /procroom/morning/api/open answered '${PR:0:80}', not the signed-out JSON -- it did not mount"; restore; }
  printf '%s' "$PR" | grep -q '"open"' && { echo "    the new door gave a count to a signed-out call"; restore; }
  echo "    the new door /procroom/morning/api/open answers a signed-out call with ok:false and no open field (mounted; reads nothing)"
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

if [ -z "$REH" ]; then
  LK="$("$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); print('present' if 'lkey' in [r[1] for r in c.execute('PRAGMA table_info(proc_use)')] else 'MISSING')" "$DB" 2>/dev/null || echo unread)"
  echo "    proc_use.lkey: $LK (read only)"
fi

echo
echo "WHAT THE PAGES NOW SHOW:"
echo "  - The month end (Yuvika's photos): a product retired after Shavez sorted a slip still counts as that slip's own product -- its"
echo "    quantities read 'same', the photo's rates sit on its lines, and a slip sent twice is counted once in the month's total."
echo "  - The month end: change 'Its scan' after typing rates, and the rates you typed stay on the lines of the same product."
echo "  - Nothing changes on the staff's screens."
echo "UNDO (puts procroom.py back and restarts the scan app; a column added stays, unread by the old file):"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S670_${P:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
