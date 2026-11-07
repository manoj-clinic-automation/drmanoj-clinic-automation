#!/bin/bash
# install_s743.sh -- S743_STATIONERY_PICK_ALL (board _numbers v1020 -> v1021; the Scan App chat, session 398, 07-Nov-2026; F-1160's
#   follow-up, found by the live read of S741 at 07:0x IST): a product box that already holds a name not on the list (the reader's name)
#   listed no product to pick. Now the note comes first and, when the text matches nothing, every product is listed under it (the nearest
#   first). ONE file: /root/assetapp/stationery.py (S741's TO) -> TO, rebuilt on the box by make_s743.py (2 counted edits) and checked
#   against the kit's whole file. No data step; no table; restarts assetapp only.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S743_STATIONERY_PICK_ALL/install_s743.sh
set -u
KIT="S743_STATIONERY_PICK_ALL"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S743_APP_DIR:-/root/assetapp}"
SERVICE="${S743_SERVICE:-assetapp}"
HEALTH="${S743_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S743_PYTHON:-python3}"
RESTART="${S743_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S743_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S743_HOST:-srv1746119}"
REH="${S743_REHEARSAL:-}"
if [ -z "${S743_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S743_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S743_HEALTH_TRIES:-20}"
FILES="stationery.py"
READONLY="asset_register.py clinic_papers.py asset_machine.py procroom.py batteries.py xray_costs.py claude_reader.py claude_reread.py sorting_desk.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s743tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S743_FAKE_HEALTH:-}" ]; then echo "$S743_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s743.py edits_s743.py walk_s743_app.py stationery.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; T="$(pin PIN_TO_$(base $f).txt)"
  [ ${#FR} -eq 32 ] && [ ${#T} -eq 32 ] || die "the kit's pins for $f are missing"
  [ "$(md5 "$HERE/$f")" = "$T" ] || die "the kit's $f is not at its TO pin"
  [ -f "$APP/$f" ] || die "$APP/$f missing"; done
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
NTO=0
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] && NTO=$((NTO+1)); done
if [ "$NTO" = 1 ]; then echo "$KIT: ALREADY INSTALLED (the file at the kit's TO pin)"; exit 0; fi
for f in $FILES; do L="$(md5 "$APP/$f")"; FR="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$FR" ] || die "$f is ${L:0:8}, not the pinned ${FR:0:8} -- another kit moved it; S743 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s743work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "the kit's file rebuilt on the pinned FROM bytes, equal to the kit's TO"
"$PY" -B "$HERE/make_s743.py" "$WORK/from/stationery.py" "$WORK/to/stationery.py" --expect | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f" 2>/dev/null)" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is not its TO pin"; done
echo "    the TO file = its pin and compiles"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s743_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s743_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { sed 's/^/    /' "$WORK/capp.txt" | cut -c1-170; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"

if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "the backup beside the live file"
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S743_${FR:0:8}" || die "backup of $f failed"; echo "    $f.bak_S743_${FR:0:8}"; done

restore(){
  echo "RESTORING the file from its backup"
  for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S743_${FR:0:8}" "$APP/$f"; done
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S743_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  BACK=0; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base $f).txt)" ] && BACK=$((BACK+1)); done
  echo "    the file back: $BACK of 1 · healthz $RH after the restore"
  [ "$BACK" = 1 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE: the .bak_S743_ files in $APP are the way back"
  exit 1
}

log "place (through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s743tmp" && mv -f "$APP/$f.s743tmp" "$APP/$f" || restore
  [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore
  echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health and the desk"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S743_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/desk")"; [ -n "${S743_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S743_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /desk answered ${X:-nothing}, not 302"; restore; }
echo "    /desk 302 (the login door: mounted)"
if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -cE 'NOT mounted|NOT wrapped')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted / NOT wrapped since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

echo
echo "WHAT THE STATIONERY PAGES NOW SHOW (your login and Shavez's):"
echo "  - A product box holding a name that is not on the list (as read from the paper): tap it -- the note says so, and every product"
echo "    is listed under it, the nearest first; one tap picks the right one. A box whose text matches products lists them, as before."
echo "UNDO (puts the file back and restarts the scan app):"
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S743_${FR:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
