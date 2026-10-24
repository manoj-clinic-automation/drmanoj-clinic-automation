#!/bin/bash
# install_s635.sh -- S635_PROCROOM_ORDERS (D773 Kit 2; board _numbers v639 -> v640; built in the Scan App chat, session 346, 24-Oct-2026).
#   The procedure-room goods, Kit 2: on the sorting desk a Procedure room paper may be marked "Dr Manoj's order" (it counts nothing),
#   and a slip is joined to its order (pre-chosen; its lines filled from the order on one tap -- he corrects); on his page, Orders and
#   deliveries (awaiting after his days; a slip with no order, from this install on); his MONTH END page -- Yuvika's WhatsApp photos
#   added and kept, read by the scan app's own reader (unchanged), matched to their scans and orders, the flags, his Save puts his rates
#   on the lines. No rupee on any staff screen.
#   sorting_desk.py (9 counted edits), procroom.py (Kit 1's file replaced whole; its FROM pinned). assets.db ADDITIVE: two new tables
#   (proc_paper, proc_photo) made by the part's own ensure() at mount; the data step writes one setting (procroom.orders_from), once.
#   Photos are kept under the uploads folder in procroom_month/ (made when the first photo is added). Restarts assetapp only.
# BUILD_NORM_v1 s3 order: gates -> the build lock -> pins (TO = ALREADY INSTALLED; else FROM; the read-only files) -> rebuild from the
# live bytes (make_s635.py) -> the TO pins -> compile -> the walk on the REAL app (every part, a COPY of the live database, made-up rows)
# on the TO files + the control on the live FROM files (must be red) -- DRY=1 stops here -> backups beside the files and of the database
# -> place -> md5 read-back -> restart assetapp -> /healthz 200, /procroom 302, the new door /procroom/month/photos answers a logged-out
# POST with 302, no part NOT mounted in the log -> the data step (the floor, once) -> what the pages now show -> undo line.
# A failure after placing puts both files back byte-identically and restarts.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S635_PROCROOM_ORDERS/install_s635.sh
set -u
KIT="S635_PROCROOM_ORDERS"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S635_APP_DIR:-/root/assetapp}"
SERVICE="${S635_SERVICE:-assetapp}"
HEALTH="${S635_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S635_PYTHON:-python3}"
RESTART="${S635_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S635_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S635_HOST:-srv1746119}"
REH="${S635_REHEARSAL:-}"
if [ -z "${S635_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S635_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S635_HEALTH_TRIES:-20}"
FILES="sorting_desk.py procroom.py"
READONLY="clinic_papers.py asset_register.py asset_machine.py stationery.py batteries.py xray_costs.py claude_reader.py claude_reread.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s635tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S635_FAKE_HEALTH:-}" ]; then echo "$S635_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s635.py walk_s635_app.py procroom.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
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
  echo "$KIT: ALREADY INSTALLED (sorting_desk.py and procroom.py at the kit's TO pins)"
  for f in $FILES; do echo "  PIN $f $(md5 "$APP/$f")"; done
  exit 0
fi
for f in $FILES; do L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S635 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s635work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "rebuild from the live bytes (counted edits), the new procroom.py, and the TO pins"
"$PY" -B "$HERE/make_s635.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"; done
for f in $FILES; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    the TO files = their pins and compile"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s635_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s635_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { cat "$WORK/capp.txt"; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "backups beside the live files, and of the database"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S635_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S635_${P:0:8}"; done
STAMP="$(date '+%Y%m%d_%H%M%S')"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S635_$STAMP" || die "the database backup failed"
echo "    $(basename "$DB").bak_S635_$STAMP"

restore(){
  echo "RESTORING sorting_desk.py and procroom.py from their backups"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S635_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S635_ copies beside them are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S635_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (through temporary files) and read back"
for f in procroom.py sorting_desk.py; do cp -p "$WORK/to/$f" "$APP/$f.s635tmp" && mv -f "$APP/$f.s635tmp" "$APP/$f" || restore; done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health, the page and the new door"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S635_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/procroom")"; [ -n "${S635_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S635_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /procroom answered ${X:-nothing}, not 302"; restore; }
echo "    /procroom 302 (the login door: the page is mounted)"
if [ -z "$REH" ]; then
  PR="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST "${HEALTH%/healthz}/procroom/month/photos" 2>/dev/null || true)"
  [ "$PR" = "302" ] || { echo "    the new door /procroom/month/photos answered ${PR:-nothing}, not 302 -- it did not mount"; restore; }
  echo "    the new door /procroom/month/photos answers 302 to a logged-out POST (mounted; writes nothing)"
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
  NB="$(nginx -T 2>/dev/null | grep -o 'client_max_body_size[^;]*' | sort -u | tr '\n' ' ' || true)"
  [ -n "$NB" ] || NB="not found in the web server settings (if it is the 1 MB default, add the photos one at a time)"
  echo "    the web server upload limit (read only): $NB"
fi

log "the data step: from now on, a slip with no order is said so (procroom.py --floor), once"
"$PY" -B "$APP/procroom.py" --floor "$DB" | sed 's/^/    /'
[ "${PIPESTATUS[0]}" = 0 ] || echo "    !! the data step did not finish -- the pages work; 'no order' stays silent until this line is run again"
echo
echo "WHAT THE PAGES NOW SHOW:"
echo "  - the sorting desk (you and Shavez), with 'Procedure room' chosen: 'A slip or a bill (it counts)' or 'Dr Manoj's order (it counts"
echo "    nothing)' with its book page number; for a slip, 'Against order' pre-chosen and 'Fill the lines from this order'. No rupee, no rate."
echo "  - your Procedure room page: 'Orders and deliveries' (awaiting after 3 days -- yours to change; part came; no order) and a link"
echo "    'Month end — Yuvika's WhatsApp' -- https://followup.dr-manoj.in/scanapp/procroom/month"
echo "    add the month's photos; each is read and matched to its scan and order; open a slip, correct it, Save -- the rates go on the lines."
echo "UNDO (puts the two files back and restarts the scan app; the new tables, the setting and any photos stay, unread):"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S635_${P:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
