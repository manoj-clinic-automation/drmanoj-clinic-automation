#!/bin/bash
# install_s627.sh -- S627_LATE_FOLLOWS_MONTH (board _numbers v602 -> v603; built in the Scan App chat, session 337, 22-Oct-2026).
#   (1) the old 'late' mark follows S625's month rule: asset_register._set_late marks a paper that counts in an earlier month than its
#       scan (clinic_papers.MONTH_OF) as late for that month -- the All papers badge, the paper page's line, the /purchases late count;
#   (2) the desk's The month page states the rule (sorting_desk.py, one sentence).
# Files: /root/assetapp/asset_register.py f21ae7ca (S625's TO; 1 counted edit), /root/assetapp/sorting_desk.py 110335ea (1 counted edit).
# Read only, pinned: clinic_papers.py (S625's TO), S624's three TO files, xray_costs.py. No database change. Restarts assetapp only.
# Order (BUILD_NORM_v1 s3): gates -> lock -> pins -> rebuild (make_s627.py) -> TO pins -> compile -> the walk on the REAL app (TO files)
# on a COPY of the live database + its control on the FROM files, and S624's and S625's real-app walks on the new app -- DRY=1 stops
# here -> backups -> place -> read back -> restart -> /healthz 200, the pages 302, no part 'NOT mounted' -> what the pages show -> undo.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S627_LATE_FOLLOWS_MONTH/install_s627.sh
set -u
KIT="S627_LATE_FOLLOWS_MONTH"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S627_APP_DIR:-/root/assetapp}"
SERVICE="${S627_SERVICE:-assetapp}"
HEALTH="${S627_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S627_PYTHON:-python3}"
RESTART="${S627_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S627_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S627_HOST:-srv1746119}"
REH="${S627_REHEARSAL:-}"
if [ -z "${S627_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S627_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S627_HEALTH_TRIES:-20}"
FILES="asset_register.py sorting_desk.py"
READONLY="clinic_papers.py batteries.py asset_machine.py stationery.py xray_costs.py"
KITS="$(cd "$HERE/.." && pwd)"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""; PLACED=0
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s627tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S627_FAKE_HEALTH:-}" ]; then echo "$S627_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

healstep(){
  log "the data step: papers scanned since S625's switch-on and read before S627 get their 'late' mark (fills empty marks only; repeatable)"
  "$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S627_$(date +%Y%m%d_%H%M%S)" || { echo "    the database backup failed -- the mark is left to each paper's next reading / Save; paste the line again to finish"; return 1; }
  echo "    the database first: $(basename "$DB").bak_S627_<stamp>"
  "$PY" -B "$HERE/heal_s627.py" "$DB" "$APP" 2>&1 | sed 's/^/    /' | cut -c1-400
  [ "${PIPESTATUS[0]}" = 0 ] || { echo "    the step failed (one transaction: nothing of it was written) -- paste the line again to finish"; return 1; }
}

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s627.py walk_s627_app.py heal_s627.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for w in S624_SCANAPP_SMALL_FIXES/walk_s624_app.py S625_MONTH_AND_DAY/walk_s625_app.py; do [ -f "$KITS/$w" ] || die "the earlier walk $w is not beside this kit"; done
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
  healstep || exit 1
  echo "$KIT: ALREADY INSTALLED (the two files at the kit's TO pins; the data step re-run above)"
  for f in $FILES; do echo "  PIN $f $(md5 "$APP/$f")"; done
  exit 0
fi
for f in $FILES; do L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; S627 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s627work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "rebuild from the live bytes (counted edits) and the TO pins"
"$PY" -B "$HERE/make_s627.py" "$WORK/from" "$WORK/to" | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is $(md5 "$WORK/to/$f" | cut -c1-8), not the TO pin"; done
for f in $FILES; do "$PY" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$WORK/to/$f" || die "$f does not compile"; done
echo "    both TO files = their pins and compile"

log "the walk on the REAL app (TO files) on a COPY of the live database -- made-up rows only -- and the control on the FROM files"
"$PY" -B "$HERE/walk_s627_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/w.txt" 2>&1; WR=$?
sed 's/^/    /' "$WORK/w.txt" | cut -c1-160
[ "$WR" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s627_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/c.txt" 2>&1 || { cat "$WORK/c.txt"; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/c.txt")"
mkdir -p "$WORK/new"; for f in "$APP"/*.py "$APP"/*.js "$APP"/*.json; do [ -f "$f" ] && cp -p "$f" "$WORK/new/"; done; cp -p "$WORK/to/"*.py "$WORK/new/"
"$PY" -B "$KITS/S624_SCANAPP_SMALL_FIXES/walk_s624_app.py" --live "$WORK/new" --files "$WORK/new" --db "$DB" > "$WORK/w624.txt" 2>&1 || { cat "$WORK/w624.txt"; die "S624's walk is not green on the new app"; }
echo "    S624's real-app walk on the new app: $(tail -1 "$WORK/w624.txt")"
"$PY" -B "$KITS/S625_MONTH_AND_DAY/walk_s625_app.py" --live "$WORK/new" --files "$WORK/new" --db "$DB" > "$WORK/w625.txt" 2>&1 || { cat "$WORK/w625.txt"; die "S625's walk is not green on the new app"; }
echo "    S625's real-app walk on the new app: $(tail -1 "$WORK/w625.txt")"
if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backups; nothing placed"; exit 0; fi

log "backups beside each live file"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S627_${P:0:8}" || die "backup of $f failed"; echo "    $f.bak_S627_${P:0:8}"; done

restore(){
  echo "RESTORING the two files from their backups"
  RB=0; for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S627_${P:0:8}" "$APP/$f"; [ "$(md5 "$APP/$f")" = "$P" ] || RB=1; done
  [ "$RB" = 0 ] || echo "    !! A FILE DID NOT COME BACK TO ITS FROM PIN -- the .bak_S627_ copies beside it are the way back"
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S627_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  for f in $FILES; do echo "    $f back at $(md5 "$APP/$f" | cut -c1-8)"; done
  echo "    healthz $RH after the restore"
  [ "$RB" = 0 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE (see above)"; exit 1
}

log "place (each through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s627tmp" && mv -f "$APP/$f.s627tmp" "$APP/$f" || restore; done
PLACED=1
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore; echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health, the pages and the log"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S627_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
for pg in stationery batteries papers/month bills/1 desk/month; do
  X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/$pg")"; [ -n "${S627_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S627_SLEEP:-2}"; done
  [ "$X" = "302" ] || { echo "    /$pg answered ${X:-nothing}, not 302"; restore; }
  echo "    /$pg 302 (the login door: the page is mounted)"
done

if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c 'NOT mounted')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi
healstep || { echo "$KIT: DONE IN CODE -- the data step did not finish (see above); paste the same line again"; exit 1; }
echo
echo "WHAT THE PAGES NOW SHOW:"
echo "  - a paper scanned since S625 whose bill is dated in an earlier month carries the amber 'late' mark for that month (All papers,"
echo "    its own page), and counts in the late number on the purchases page -- as a late bill always has;"
echo "  - the desk's The month page states the rule: from 22-Oct-2026 a bill dated earlier than its scan counts in its own month."
echo "UNDO (puts the two files back and restarts the scan app):"
for f in $FILES; do P="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S627_${P:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
