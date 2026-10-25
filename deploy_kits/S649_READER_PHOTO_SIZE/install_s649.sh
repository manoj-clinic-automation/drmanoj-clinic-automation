#!/bin/bash
# install_s649.sh -- S649_READER_PHOTO_SIZE (board _numbers v685 -> v686; built in the Scan App chat, session 352, 25-Oct-2026).
#   F-1003: a phone photo over the reader's image limit was never made smaller -- claude_reader._smaller imported Pillow in the
#   service's own python (the system python3, which has none) and sent the photo whole, to be refused ("read failed" on the desk).
#   Now it falls back to the venv python (TURN_PY) exactly as turn_file does; the stored scan is never changed. claude_reader.py
#   replaced whole (its FROM pinned: the live 10118909); no other file; no data step; restarts assetapp only. Same order and gates
#   as S648's installer (BUILD_NORM_v1 s3). Two walks before anything is placed: the reader's own (in the service python, made-up
#   photos) with its control on the live reader, and S648's walk of the whole app with the new reader in it.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S649_READER_PHOTO_SIZE/install_s649.sh
set -u
KIT="S649_READER_PHOTO_SIZE"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S649_APP_DIR:-/root/assetapp}"
SERVICE="${S649_SERVICE:-assetapp}"
HEALTH="${S649_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S649_PYTHON:-python3}"
TURN="${S649_TURN_PY:-/root/wa/venv/bin/python3}"
RESTART="${S649_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S649_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S649_HOST:-srv1746119}"
REH="${S649_REHEARSAL:-}"
if [ -z "${S649_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
if [ -z "${S649_TURN_PY:-}" ]; then                                    # K1: the service's own S618_TURN_PY, when it sets one
  TURN0="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null | tr ' ' '\n' | sed -n 's/^S618_TURN_PY=//p' | head -1)"
  [ -n "$TURN0" ] && TURN="$TURN0"
fi
if [ -z "${S649_PYTHON:-}" ] && [ -z "$REH" ]; then                   # K1: walk in the very python the running service uses
  MP="$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null || echo 0)"
  if [ "${MP:-0}" -gt 0 ] 2>/dev/null; then SP0="$(readlink -f /proc/$MP/exe 2>/dev/null || true)"; [ -x "$SP0" ] && "$SP0" -c "import flask" 2>/dev/null && PY="$SP0"; fi
fi
DB="${S649_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S649_HEALTH_TRIES:-20}"
FILES="claude_reader.py"
READONLY="procroom.py sorting_desk.py clinic_papers.py asset_register.py asset_machine.py stationery.py batteries.py xray_costs.py claude_reread.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s649tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S649_FAKE_HEALTH:-}" ]; then echo "$S649_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files, the two pythons)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s649.py walk_s649_reader.py walk_s648_app.py claude_reader.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for f in $FILES; do for k in PIN_FROM_$(base $f).txt PIN_TO_$(base $f).txt; do v="$(pin $k)"; [ ${#v} -eq 32 ] || die "$k is missing in the kit"; done; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ "$(md5 "$HERE/claude_reader.py")" = "$(pin PIN_TO_claude_reader.txt)" ] || die "the kit's claude_reader.py is not at its pin"
for f in $READONLY; do v="$(pin PIN_READ_$(base $f).txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base $f).txt is missing in the kit"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
[ -x "$TURN" ] || die "no venv python at $TURN (the one that shrinks the photo)"
"$TURN" -I -c "import PIL" 2>/dev/null || die "$TURN has no Pillow"
echo "    the kit and $APP ok; the service python: $PY; $TURN has Pillow"
"$PY" -c "
import sqlite3, sys
try:
    c = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True)
    rows = c.execute(\"SELECT COALESCE(error, '?'), COUNT(*) FROM claude_reading WHERE ok=0 GROUP BY 1 ORDER BY 2 DESC\").fetchall()
    print('    the papers Claude could not read so far, by reason (read only): ' + ('; '.join('%s x%d' % (e[:60], n) for e, n in rows) or 'none'))
except Exception as e:
    print('    the papers Claude could not read so far: not counted (%s)' % type(e).__name__)
" "$DB"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (claude_reader.py at the kit's TO pin)"
  for f in $FILES; do echo "  PIN $f $(md5 "$APP/$f")"; done
  exit 0
fi
for f in $FILES; do L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S649 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s649work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to" "$WORK/app"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "the kit's claude_reader.py on the pinned FROM bytes, and its TO pin"
"$PY" -B "$HERE/make_s649.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"; done
for f in $FILES; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    the TO files = their pins and compile"

log "the reader's walk in the SERVICE python ($PY) with made-up photos -- and its control on the live reader"
"$PY" -B "$HERE/walk_s649_reader.py" --files "$WORK/to" --service-py "$(command -v "$PY")" --turn-py "$TURN" > "$WORK/wr.txt" 2>&1; WR=$?
sed 's/^/    /' "$WORK/wr.txt" | cut -c1-170
[ "$WR" = 0 ] || die "the reader's walk is not all green"
"$PY" -B "$HERE/walk_s649_reader.py" --files "$WORK/from" --service-py "$(command -v "$PY")" --turn-py "$TURN" --expect-red > "$WORK/cr.txt" 2>&1 || { cat "$WORK/cr.txt"; die "the control on the live reader is not red where it must be (is F-1003's cause on this box what the kit says?)"; }
echo "    $(tail -1 "$WORK/cr.txt")"

log "the whole app (S648's walk: every part it mounts, from a scratch folder) with the new reader in it, on a COPY of the live database"
for f in "$APP"/*.py "$APP"/*.js "$APP"/*.json; do [ -f "$f" ] && cp -p "$f" "$WORK/app/"; done
cp -p "$WORK/to/claude_reader.py" "$WORK/app/claude_reader.py"
"$PY" -B "$HERE/walk_s648_app.py" --live "$WORK/app" --files "$WORK/app" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
echo "    $(tail -1 "$WORK/wapp.txt")"
[ "$WA" = 0 ] || { sed 's/^/    /' "$WORK/wapp.txt" | grep -E '^ *RED' | cut -c1-170; die "the app's walk with the new reader is not all green"; }
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "backups beside the live file"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S649_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S649_${P:0:8}"; done

restore(){
  echo "RESTORING claude_reader.py from its backup"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S649_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S649_ copies beside them are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S649_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s649tmp" && mv -f "$APP/$f.s649tmp" "$APP/$f" || restore; done
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; chown --reference="$APP/$f.bak_S649_${P:0:8}" "$APP/$f" 2>/dev/null || true; done   # K1: the owner it had
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health, a page, and the reader's walk on the PLACED file"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S649_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/procroom")"; [ -n "${S649_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S649_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /procroom answered ${X:-nothing}, not 302"; restore; }
echo "    /procroom 302 (the login door: the app is up)"
"$PY" -B "$HERE/walk_s649_reader.py" --files "$APP" --service-py "$(command -v "$PY")" --turn-py "$TURN" > "$WORK/wr2.txt" 2>&1 || { cat "$WORK/wr2.txt"; restore; }
echo "    the placed reader: $(tail -1 "$WORK/wr2.txt")"
if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

echo
echo "WHAT CHANGES:"
echo "  - A phone photo over the reader's limit (about 3.7 MB) is now sent to the reader as a smaller copy and gets read;"
echo "    the stored scan stays as it was. A paper that says 'read failed' can be read again with its Re-read button."
echo "  - Such a photo now also gets the reader's 'how does each page lie' check; a sideways one in the pharmacy lane is turned upright"
echo "    as a NEW stored file (the old one kept), as smaller photos already are (S618)."
echo "  - Still not read: a HEIC photo (the reader takes JPG, PNG, WEBP and PDF only) -- unchanged."
echo "UNDO (puts claude_reader.py back and restarts the scan app):"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S649_${P:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
