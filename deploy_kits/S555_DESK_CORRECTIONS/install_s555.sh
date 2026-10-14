#!/bin/bash
# install_s555.sh -- S555_DESK_CORRECTIONS: the sorting desk's corrections (Save always on screen, dates dd-mm-yyyy, the
# misread-date rule, the own name read as the supplier, Claude's reading beside each box, one word per lane on the bills
# list, no Claude read of a patient's paper). No database change.
# BUILD_NORM_v1 s3 order (S551's shape): gates -> FROM pins -> rebuild from the live bytes -> TO pins -> compile (both
# pythons) -> walk + control on a scratch copy (DRY=1 stops here) -> backups -> place -> md5 read-back -> restart the named
# service only -> /healthz 200 and /desk 302 (the login gate; 302 ONLY -- S551 review K2 N1) -> what his pages now show ->
# undo line. A failure after placing restores the backups and restarts.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S555_DESK_CORRECTIONS/install_s555.sh
set -u
KIT="S555_DESK_CORRECTIONS"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S555_APP_DIR:-/root/assetapp}"
SERVICE="${S555_SERVICE:-assetapp}"
HEALTH="${S555_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S555_PYTHON:-python3}"
PYV="${S555_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S555_RESTART_CMD:-systemctl restart $SERVICE}"
SHARED="${S555_SHARED_DIR:-/root/shared}"
TRIES="${S555_HEALTH_TRIES:-20}"
FILES="sorting_desk.py claude_reread.py asset_register.py"          # placed in this order: the app's own file last
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
# the database: the environment's value when set; else the service's own (read quietly, never printed); else the app's default
if [ -z "${S555_DB:-}" ] || [ -z "${S555_UPLOADS:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  UP0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_UPLOADS=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S555_DB:-${DB0:-$APP/assets.db}}"
UP="${S555_UPLOADS:-${UP0:-$APP/uploads}}"
STAMP="$(date +%Y%m%d_%H%M%S)"

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for f in $FILES; do
  for k in FROM TO; do v="$(pin PIN_${k}_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_${k}_$(base "$f").txt is missing in the kit"; done
done
for f in make_s555.py walk_s555.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
for f in sorting_desk.py asset_register.py claude_reread.py clinic_papers.py claude_reader.py; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    $APP ok; database and uploads read from the service (not shown)"

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (the three files at the kit's pins)"
  echo "  PINS (read back): sorting_desk.py $(md5 "$APP/sorting_desk.py") . asset_register.py $(md5 "$APP/asset_register.py") . claude_reread.py $(md5 "$APP/claude_reread.py")"
  exit 0
fi
for f in $FILES; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; rebuild S555 on the new bytes"
  echo "    $f ${P:0:8} ok"
done

WORK="$(mktemp -d /tmp/s555_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"
trap 'rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.tmp"; done' EXIT

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built"
cp "$APP/sorting_desk.py" "$APP/asset_register.py" "$APP/claude_reread.py" "$APP/clinic_papers.py" "$APP/claude_reader.py" "$WORK/live_in/"
"$PY" -B "$HERE/make_s555.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
cp "$APP/clinic_papers.py" "$APP/claude_reader.py" "$WORK/built/"
for f in $FILES; do
  B="$(md5 "$WORK/built/$f")"; P="$(pin PIN_TO_$(base "$f").txt)"
  [ "$B" = "$P" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"
done

log "compile on both pythons"
mkdir -p "$WORK/cc"; for f in $FILES; do cp "$WORK/built/$f" "$WORK/cc/"; done
( cd "$WORK/cc" && "$PY" -m py_compile $FILES ) || die "a built file does not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $FILES ) || die "a built file does not compile on $PYV"; echo "    compiles on $PY and $PYV"; else echo "    compiles on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walk on a scratch copy of the database (made-up rows; nothing sent anywhere) -- and the control on the live files"
( cd "$WORK" && "$PY" -B "$HERE/walk_s555.py" "$WORK/built" "$DB" --work "$WORK/walk" --shared "$SHARED" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E '^SIZES' "$WORK/walk.txt" | head -1 | sed 's/^/    /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s555.py" "$WORK/live_in" "$DB" --work "$WORK/control" --shared "$SHARED" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | tail -1 | sed 's/^/    /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run)"; exit 0; fi

log "backups beside the live files, and the database by the backup API (no database change is made)"
for f in $FILES; do
  P="$(pin PIN_FROM_$(base "$f").txt)"; cp -p "$APP/$f" "$APP/$f.bak_S555_${P:0:8}" || die "backup of $f failed"
done
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S555_$STAMP" || die "database backup failed"
echo "    sorting_desk.py / claude_reread.py / asset_register.py .bak_S555_<from8> . $(basename "$DB").bak_S555_$STAMP"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING the three files from their backups"
  for f in $FILES; do
    P="$(pin PIN_FROM_$(base "$f").txt)"
    cp -p "$APP/$f.bak_S555_${P:0:8}" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"
  done
  eval "$RESTART" || true
  for f in $FILES; do
    [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || { echo "RESTORE FAILED ($f) -- run the UNDO line in the README"; exit 2; }
  done
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE APP DOES NOT ANSWER (healthz ${RH:-nothing}) -- the scan app is DOWN: tell Claude now"; exit 2; }
  echo "    files back at $(for f in $FILES; do printf '%s ' "$(md5 "$APP/$f" | cut -c1-8)"; done)(the FROM pins); healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays)"
  exit 1
}

log "place (the desk first, then the re-read, then the app), and read the md5 back"
for f in $FILES; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || restore; done
echo "    placed: the three files at the kit's pins"

log "restart $SERVICE only, then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S555_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
# S555 item 7 (S551 review K2 N1): a plain request to the desk must get the login redirect -- 302 ONLY. A 200 would mean the
# login gate failed open; a 404 / 500 that the desk did not mount. Anything but 302 = restore.
DESK=""; for i in $(seq 1 "$TRIES"); do DESK="$(hc "${HEALTH%/healthz}/desk")"; [ "$DESK" = "302" ] && break; sleep 2; done
if [ "$DESK" = "302" ]; then
  echo "    /desk answers 302 (the login gate -- expected, not a failure): the desk is mounted and gated"
else
  echo "    /desk answered ${DESK:-nothing}, not 302: the desk did not mount, or its login gate is open"; restore
fi

echo
echo "$KIT: DONE."
echo "  PINS (read back): sorting_desk.py $(md5 "$APP/sorting_desk.py") . asset_register.py $(md5 "$APP/asset_register.py") . claude_reread.py $(md5 "$APP/claude_reread.py")"
echo "  WHAT HIS PAGES NOW SHOW: on the sorting desk (https://followup.dr-manoj.in/scanapp/desk) the green 'Save -- next paper'"
echo "  button stays on screen on the laptop (the fields above it scroll); every date reads dd-mm-yyyy and can be typed as"
echo "  dd-mm-yyyy, d-m-yy, dd/mm/yyyy or yyyy-mm-dd; a year-old bill is no longer called 'misread'; a supplier box holding his"
echo "  own name says so and offers what Claude read; a grey 'Claude read: ... -- use it' line sits under a box when Claude"
echo "  read something different; the Purchases list shows one word per lane; Claude never reads a patient's paper."
echo "  UNDO (one line): $(for f in $FILES; do P="$(pin PIN_FROM_$(base "$f").txt)"; printf '\\cp -p %s %s && ' "$APP/$f.bak_S555_${P:0:8}" "$APP/$f"; done)systemctl restart $SERVICE"
exit 0
