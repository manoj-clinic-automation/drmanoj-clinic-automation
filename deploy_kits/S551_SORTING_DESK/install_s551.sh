#!/bin/bash
# install_s551.sh -- S551_SORTING_DESK (D722): the sorting desk, Bills awaited by supplier, the implant stock ledger, The month,
# the Switches card and the tidy-up of the scan app. Installed with the desk switched OFF for Shavez (desk.on absent).
# BUILD_NORM_v1 s3 order: gates -> FROM pins -> rebuild from the live bytes -> compile (both pythons) -> walk + control on a
# scratch copy (DRY=1 stops here) -> backups -> place -> md5 read-back -> data step (tables; desk.floor) -> restart the named
# service only -> health -> what his pages now show -> undo line. A failure after placing restores the backups and restarts.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S551_SORTING_DESK/install_s551.sh
set -u
KIT="S551_SORTING_DESK"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S551_APP_DIR:-/root/assetapp}"
SERVICE="${S551_SERVICE:-assetapp}"
HEALTH="${S551_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S551_PYTHON:-python3}"
PYV="${S551_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S551_RESTART_CMD:-systemctl restart $SERVICE}"
SHARED="${S551_SHARED_DIR:-/root/shared}"
TRIES="${S551_HEALTH_TRIES:-20}"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
FROM_AR="$(pin PIN_FROM_asset_register.txt)"; FROM_CP="$(pin PIN_FROM_clinic_papers.txt)"
TO_AR="$(pin PIN_TO_asset_register.txt)"; TO_CP="$(pin PIN_TO_clinic_papers.txt)"; TO_SD="$(pin PIN_TO_sorting_desk.txt)"
# the database and the uploads folder: the environment's value when set; else the service's own (read quietly, never printed)
if [ -z "${S551_DB:-}" ] || [ -z "${S551_UPLOADS:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  UP0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_UPLOADS=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S551_DB:-${DB0:-$APP/assets.db}}"
UP="${S551_UPLOADS:-${UP0:-$APP/uploads}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
TODAY_IST="$(TZ=Asia/Kolkata date +%F)"

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for v in "$FROM_AR" "$FROM_CP" "$TO_AR" "$TO_CP" "$TO_SD"; do [ ${#v} -eq 32 ] || die "a PIN file is missing in the kit"; done
for f in make_s551.py walk_s551.py sorting_desk.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
[ "$(md5 "$HERE/sorting_desk.py")" = "$TO_SD" ] || die "the kit's sorting_desk.py is not at its pin"
for f in asset_register.py clinic_papers.py claude_reader.py claude_reread.py; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    $APP ok; database and uploads read from the service (not shown)"

log "pins -- the live bytes must be the ones this kit was built on"
if [ "$(md5 "$APP/asset_register.py")" = "$TO_AR" ] && [ "$(md5 "$APP/clinic_papers.py")" = "$TO_CP" ] && [ -f "$APP/sorting_desk.py" ] && [ "$(md5 "$APP/sorting_desk.py")" = "$TO_SD" ]; then
  echo "$KIT: ALREADY INSTALLED (the three files at the kit's pins)"
  echo "  PINS (read back): asset_register.py $(md5 "$APP/asset_register.py") . clinic_papers.py $(md5 "$APP/clinic_papers.py") . sorting_desk.py $(md5 "$APP/sorting_desk.py")"
  exit 0
fi
L="$(md5 "$APP/asset_register.py")"; [ "$L" = "$FROM_AR" ] || die "asset_register.py is ${L:0:8}, not the pinned ${FROM_AR:0:8} -- another kit moved it; rebuild S551 on the new bytes"
L="$(md5 "$APP/clinic_papers.py")"; [ "$L" = "$FROM_CP" ] || die "clinic_papers.py is ${L:0:8}, not the pinned ${FROM_CP:0:8} -- another kit moved it; rebuild S551 on the new bytes"
[ -e "$APP/sorting_desk.py" ] && die "$APP/sorting_desk.py already exists and is not this kit's -- look before placing"
echo "    asset_register.py ${FROM_AR:0:8} ok . clinic_papers.py ${FROM_CP:0:8} ok . sorting_desk.py absent ok"

WORK="$(mktemp -d /tmp/s551_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"
trap 'rm -rf "$WORK"; rm -f "$APP/asset_register.py.tmp" "$APP/clinic_papers.py.tmp" "$APP/sorting_desk.py.tmp"' EXIT

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built"
cp "$APP/asset_register.py" "$APP/clinic_papers.py" "$APP/claude_reader.py" "$APP/claude_reread.py" "$WORK/live_in/"
"$PY" -B "$HERE/make_s551.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
cp "$APP/claude_reader.py" "$APP/claude_reread.py" "$WORK/built/"
for f in asset_register.py:$TO_AR clinic_papers.py:$TO_CP sorting_desk.py:$TO_SD; do
  n="${f%%:*}"; p="${f##*:}"; B="$(md5 "$WORK/built/$n")"
  [ "$B" = "$p" ] || die "the rebuilt $n is ${B:0:8}, the kit says ${p:0:8}"; echo "    rebuilt $n ${B:0:8} = the kit's pin"
done

log "compile on both pythons"
mkdir -p "$WORK/cc"; cp "$WORK/built/asset_register.py" "$WORK/built/clinic_papers.py" "$WORK/built/sorting_desk.py" "$WORK/cc/"
"$PY" -m py_compile "$WORK/cc/asset_register.py" "$WORK/cc/clinic_papers.py" "$WORK/cc/sorting_desk.py" || die "a built file does not compile on $PY"
if [ -x "$PYV" ]; then "$PYV" -m py_compile "$WORK/cc/asset_register.py" "$WORK/cc/clinic_papers.py" "$WORK/cc/sorting_desk.py" || die "a built file does not compile on $PYV"; echo "    compiles on $PY and $PYV"; else echo "    compiles on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walk on a scratch copy of the database (made-up rows; nothing sent anywhere) -- and the control on the live files"
( cd "$WORK" && "$PY" -B "$HERE/walk_s551.py" "$WORK/built" "$DB" --work "$WORK/walk" --shared "$SHARED" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E '^SIZES' "$WORK/walk.txt" | head -1 | sed 's/^/    /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s551.py" "$WORK/live_in" "$DB" --work "$WORK/control" --shared "$SHARED" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run)"; exit 0; fi

log "backups beside the live files, and the database by the backup API"
cp -p "$APP/asset_register.py" "$APP/asset_register.py.bak_S551_${FROM_AR:0:8}" || die "backup failed"
cp -p "$APP/clinic_papers.py" "$APP/clinic_papers.py.bak_S551_${FROM_CP:0:8}" || die "backup failed"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S551_$STAMP" || die "database backup failed"
echo "    asset_register.py.bak_S551_${FROM_AR:0:8} . clinic_papers.py.bak_S551_${FROM_CP:0:8} . $(basename "$DB").bak_S551_$STAMP"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING the two files from their backups; sorting_desk.py taken out"
  cp -p "$APP/asset_register.py.bak_S551_${FROM_AR:0:8}" "$APP/asset_register.py.tmp" && mv -f "$APP/asset_register.py.tmp" "$APP/asset_register.py"
  cp -p "$APP/clinic_papers.py.bak_S551_${FROM_CP:0:8}" "$APP/clinic_papers.py.tmp" && mv -f "$APP/clinic_papers.py.tmp" "$APP/clinic_papers.py"
  rm -f "$APP/sorting_desk.py"
  eval "$RESTART" || true
  { [ "$(md5 "$APP/asset_register.py")" = "$FROM_AR" ] && [ "$(md5 "$APP/clinic_papers.py")" = "$FROM_CP" ]; } || { echo "RESTORE FAILED -- run the UNDO line in the README"; exit 2; }
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE APP DOES NOT ANSWER (healthz ${RH:-nothing}) -- the scan app is DOWN: tell Claude now"; exit 2; }
  echo "    files back at ${FROM_AR:0:8} / ${FROM_CP:0:8}; healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays; the new tables, if made, are read by nothing)"
  exit 1
}

log "place (the new module first, then clinic_papers, then the app), and read the md5 back"
for f in sorting_desk.py clinic_papers.py asset_register.py; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
[ "$(md5 "$APP/asset_register.py")" = "$TO_AR" ] && [ "$(md5 "$APP/clinic_papers.py")" = "$TO_CP" ] && [ "$(md5 "$APP/sorting_desk.py")" = "$TO_SD" ] || restore
echo "    placed: the three files at the kit's pins"

log "data step: the desk's tables and columns; desk.floor = today if absent (old scans do not flood the list)"
OUT="$(cd "$WORK" && "$PY" -B "$APP/sorting_desk.py" --ensure "$DB" --floor "$TODAY_IST" 2>&1)" || { echo "$OUT" | tail -5; restore; }
echo "    $OUT"

log "restart $SERVICE only, then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S551_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
DESK="$(hc "${HEALTH%/healthz}/desk")"
echo "    /desk answers ${DESK:-nothing} to a plain request (302 = the login gate -- expected, not a failure)"

ON="$("$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); r=c.execute(\"SELECT value FROM settings WHERE key='desk.on'\").fetchone(); print(r[0] if r else 'absent')" "$DB" 2>/dev/null)"
echo
echo "$KIT: DONE."
echo "  PINS (read back): asset_register.py $(md5 "$APP/asset_register.py") . clinic_papers.py $(md5 "$APP/clinic_papers.py") . sorting_desk.py $(md5 "$APP/sorting_desk.py")"
echo "  WHAT HIS PAGES NOW SHOW: the header reads 'Scan app & assets'; the front page has a Switches card (smart scanner,"
echo "  reception buttons, sorting desk for Shavez); the sorting desk is at https://followup.dr-manoj.in/scanapp/desk with"
echo "  Bills awaited, the Implant stock ledger and The month beside it. desk.on is $ON -- the desk is OFF for Shavez until"
echo "  Dr Manoj switches it on (the card on the front page); Dr Manoj can use it now."
echo "  UNDO (one line): cp -p $APP/asset_register.py.bak_S551_${FROM_AR:0:8} $APP/asset_register.py && cp -p $APP/clinic_papers.py.bak_S551_${FROM_CP:0:8} $APP/clinic_papers.py && rm -f $APP/sorting_desk.py && systemctl restart $SERVICE"
exit 0
