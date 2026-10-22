#!/bin/bash
# install_s624.sh -- S624_SCANAPP_SMALL_FIXES (board _numbers v595 -> v596; built in the Scan App chat, session 337, 22-Oct-2026).
#   F-977 a battery past its warranty shows "Out of warranty since dd-mm-yyyy", not OK (batteries.py, 1 counted edit);
#   F-978 a machine's cover or part takes its paper AFTER it was added -- the spends' link box (asset_machine.py, 6 counted edits);
#   F-979 a stationery line of N single pieces of an item counted in packets of N is named in the desk Save's words and marked on
#         the owner's Stationery page (stationery.py, 4 counted edits). The desk's own screen code (sorting_desk.py) is NOT touched.
# No database change (no new table or column; the new routes write the columns S557 made). Restarts assetapp only.
# BUILD_NORM_v1 s3 order: gates -> the build lock -> pins (TO = ALREADY INSTALLED; else FROM; the read-only files) -> rebuild from the
# live bytes (make_s624.py) -> TO pins -> compile (the service's python3) -> the walk on the TO files + the control on the live FROM
# files (must be red) -- DRY=1 stops here -> backups beside each file -> place -> md5 read-back -> restart assetapp -> /healthz 200,
# then /stationery, /batteries, /assets/1 answer 302 -> what the pages now show -> undo line. A failure after placing puts all
# three files back byte-identically and restarts assetapp.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S624_SCANAPP_SMALL_FIXES/install_s624.sh
set -u
KIT="S624_SCANAPP_SMALL_FIXES"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S624_APP_DIR:-/root/assetapp}"
SERVICE="${S624_SERVICE:-assetapp}"
HEALTH="${S624_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S624_PYTHON:-python3}"
RESTART="${S624_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S624_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S624_HOST:-srv1746119}"
REH="${S624_REHEARSAL:-}"
if [ -z "${S624_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S624_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S624_HEALTH_TRIES:-20}"
FILES="batteries.py asset_machine.py stationery.py"
READONLY="sorting_desk.py asset_register.py xray_costs.py clinic_papers.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""; PLACED=0
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s624tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S624_FAKE_HEALTH:-}" ]; then echo "$S624_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s624.py walk_s624.py walk_s624_app.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for f in $FILES; do for k in PIN_FROM_$(base $f).txt PIN_TO_$(base $f).txt; do v="$(pin $k)"; [ ${#v} -eq 32 ] || die "$k is missing in the kit"; done; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
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
  echo "$KIT: ALREADY INSTALLED (the three files at the kit's TO pins)"
  for f in $FILES; do echo "  PIN $f $(md5 "$APP/$f")"; done
  exit 0
fi
for f in $FILES; do L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S624 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s624work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "rebuild from the live bytes (counted edits) and the TO pins"
"$PY" -B "$HERE/make_s624.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"; done
for f in $FILES; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    the three TO files = their pins and compile"

log "the walk on the TO files (a stand-in app, made-up rows) and the control on the live FROM files (must be red)"
"$PY" -B "$HERE/walk_s624.py" --app "$WORK/to" > "$WORK/walk.txt" 2>&1; WR=$?
grep -E '^(GREEN|RED)' "$WORK/walk.txt" | cut -c1-150 | sed 's/^/    /'; tail -1 "$WORK/walk.txt" | sed 's/^/    /'
[ "$WR" = 0 ] || die "the walk is not all green"
"$PY" -B "$HERE/walk_s624.py" --app "$WORK/from" --expect-red > "$WORK/ctl.txt" 2>&1 || { cat "$WORK/ctl.txt"; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/ctl.txt")"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s624_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-160
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s624_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { cat "$WORK/capp.txt"; die "the real-app control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backups; nothing placed"; exit 0; fi

log "backups beside each live file"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S624_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S624_${P:0:8}"; done

restore(){
  echo "RESTORING the three files from their backups"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S624_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S624_ copies beside it are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S624_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (each through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s624tmp" && mv -f "$APP/$f.s624tmp" "$APP/$f" || restore; done
PLACED=1
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health and the three pages"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S624_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
for pg in stationery batteries assets/1; do
  X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/$pg")"; [ -n "${S624_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S624_SLEEP:-2}"; done
  [ "$X" = "302" ] || { echo "    /$pg answered ${X:-nothing}, not 302"; restore; }
  echo "    /$pg 302 (the login door: the page is mounted)"
done

if [ -z "$REH" ]; then
  PR="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST "${HEALTH%/healthz}/assets/1/covers/1/paper" 2>/dev/null || true)"
  [ "$PR" = "302" ] || { echo "    the new cover-paper route answered ${PR:-nothing}, not 302 -- the machine part did not mount"; restore; }
  echo "    the new cover-paper route answers 302 (the machine part is mounted)"
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi
echo
echo "WHAT THE PAGES NOW SHOW:"
echo "  - Batteries (https://followup.dr-manoj.in/scanapp/batteries): a battery whose warranty has passed reads 'Out of warranty since dd-mm-yyyy' in grey, not OK;"
echo "  - a machine's page (Assets -> the machine): in Cover history and Parts, a row with no paper has a small 'B-____ link' box, as Spends had;"
echo "  - the sorting desk's Save words, and the owner's Stationery page, say 'check the quantity' when a line looks like single pieces of an item counted in packets."
echo "UNDO (puts the three files back and restarts the scan app):"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S624_${P:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
