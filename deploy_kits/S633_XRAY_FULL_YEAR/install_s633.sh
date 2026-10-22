#!/bin/bash
# install_s633.sh -- S633_XRAY_FULL_YEAR (D767; board _numbers v618 -> v619; built in the Scan App chat, session 341, 22-Oct-2026).
#   The X-ray costs page (owner only): the financial year from April, month by month; an AMC / CMC / insurance with a cost spread over
#   its months; a battery's price (less the old battery) spread over its place's usual life; "Film purchases by size" with the running
#   boxes and rupees of each size; the film bills kept on the Machines list counted once their lines are typed (new door /xray/film).
#   xray_costs.py only (21 counted edits). assets.db ADDITIVE: one new table xray_film_line, made by the part's own ensure() at mount.
#   Restarts assetapp only.
# BUILD_NORM_v1 s3 order: gates -> the build lock -> pins (TO = ALREADY INSTALLED; else FROM; the read-only files) -> rebuild from the
# live bytes (make_s633.py) -> the TO pin -> compile -> the walk on the REAL app (every part, a COPY of the live database, made-up
# rows) on the TO file + the control on the live FROM file (must be red) -- DRY=1 stops here -> backup beside the file -> place ->
# md5 read-back -> restart assetapp -> /healthz 200, /xray 302, the new door answers a logged-out POST with 302, no part NOT mounted
# in the log -> what the page now shows -> undo line. A failure after placing puts the file back byte-identically and restarts.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S633_XRAY_FULL_YEAR/install_s633.sh
set -u
KIT="S633_XRAY_FULL_YEAR"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S633_APP_DIR:-/root/assetapp}"
SERVICE="${S633_SERVICE:-assetapp}"
HEALTH="${S633_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S633_PYTHON:-python3}"
RESTART="${S633_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S633_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S633_HOST:-srv1746119}"
REH="${S633_REHEARSAL:-}"
if [ -z "${S633_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S633_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S633_HEALTH_TRIES:-20}"
FILES="xray_costs.py"
READONLY="batteries.py asset_register.py sorting_desk.py clinic_papers.py asset_machine.py stationery.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s633tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S633_FAKE_HEALTH:-}" ]; then echo "$S633_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s633.py walk_s633_app.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
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
  echo "$KIT: ALREADY INSTALLED (xray_costs.py at the kit's TO pin)"
  for f in $FILES; do echo "  PIN $f $(md5 "$APP/$f")"; done
  exit 0
fi
for f in $FILES; do L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S633 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s633work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "rebuild from the live bytes (counted edits) and the TO pin"
"$PY" -B "$HERE/make_s633.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"; done
for f in $FILES; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    the TO file = its pin and compiles"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s633_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s633_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { cat "$WORK/capp.txt"; die "the control on the live file is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "backup beside the live file"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S633_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S633_${P:0:8}"; done

restore(){
  echo "RESTORING xray_costs.py from its backup"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S633_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! THE FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S633_ copy beside it is the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S633_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s633tmp" && mv -f "$APP/$f.s633tmp" "$APP/$f" || restore; done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health, the page and the new door"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S633_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/xray")"; [ -n "${S633_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S633_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /xray answered ${X:-nothing}, not 302"; restore; }
echo "    /xray 302 (the login door: the page is mounted)"
if [ -z "$REH" ]; then
  PR="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST "${HEALTH%/healthz}/xray/film" 2>/dev/null || true)"
  [ "$PR" = "302" ] || { echo "    the new door /xray/film answered ${PR:-nothing}, not 302 -- it did not mount"; restore; }
  echo "    the new door /xray/film answers 302 to a logged-out POST (mounted; writes nothing)"
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi
echo
echo "WHAT THE PAGE NOW SHOWS (https://followup.dr-manoj.in/scanapp/xray):"
echo "  - 'This financial year' from April, month by month: films, AMC and service, batteries, papers marked, total;"
echo "  - the AMC spread evenly over its months; a battery's cost spread over its place's usual life;"
echo "  - 'Film purchases by size' with the running boxes and rupees of each size;"
echo "  - 'Film bills kept on the Machines list': type each bill's lines and it counts as film on its date."
echo "UNDO (puts the file back and restarts the scan app; the new table xray_film_line stays, unread):"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S633_${P:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
