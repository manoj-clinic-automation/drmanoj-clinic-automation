#!/bin/bash
# install_s559.sh -- S559_ONE_ROAD: one easy road through the scan app. One menu bar on every owner / manager page and on the
# desk's four pages (Sorting desk (N) . The month . Bills awaited (N) . Implant ledger . Machines . Renewals . All papers .
# Vendors . Admin . account . Logout); the home page opens with the desk's card; /desk?open=<id>; every non-pharmacy paper row
# leads to the desk; the old bill page shows its scan, a desk button and a true badge; one meaning of "waiting"; one route
# each; BACK to the scan app's home; the small things (Zone once, dd-mm-yyyy, the old record's cover, Renewals' Kind, the PM
# sentence); and the scanner's Adjust / Save fix (one paper, one stamp) inside the intake-only branches. NO database change.
# BUILD_NORM_v1 s3 order (S557's shape): gates -> FROM pins (and the readers) -> rebuild from the live bytes -> TO pins ->
# compile (both pythons) -> baseline + walk + control + the S557, S555 and S551 walks on a scratch copy (DRY=1 stops here) ->
# backups (files, and the database by the backup API) -> place -> md5 read-back -> restart the named service only ->
# /healthz 200, /desk 302 (the login gate; 302 ONLY), the served widget carries S559.1 -> what his pages now show -> undo line.
# A failure after placing restores.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S559_ONE_ROAD/install_s559.sh
set -u
KIT="S559_ONE_ROAD"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KITS="${S559_KITS_DIR:-$(cd "$HERE/.." && pwd)}"
APP="${S559_APP_DIR:-/root/assetapp}"
SERVICE="${S559_SERVICE:-assetapp}"
HEALTH="${S559_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S559_PYTHON:-python3}"
PYV="${S559_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S559_RESTART_CMD:-systemctl restart $SERVICE}"
SHARED="${S559_SHARED_DIR:-/root/shared}"
TRIES="${S559_HEALTH_TRIES:-20}"
FILES="asset_machine.py sorting_desk.py clinic_papers.py scanner_widget.js asset_register.py"   # rebuilt from the live bytes; placed in this order, the app's own file last
PYFILES="asset_machine.py sorting_desk.py clinic_papers.py asset_register.py"
READERS="claude_reader.py claude_reread.py"                                                    # read only; pinned (the walks import them)
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
if [ -z "${S559_DB:-}" ] || [ -z "${S559_UPLOADS:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  UP0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_UPLOADS=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S559_DB:-${DB0:-$APP/assets.db}}"
UP="${S559_UPLOADS:-${UP0:-$APP/uploads}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
W557="$KITS/S557_MACHINE_PAGES/walk_s557.py"
W555="$KITS/S555_DESK_CORRECTIONS/walk_s555.py"
W551="$KITS/S551_SORTING_DESK/walk_s551.py"

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for f in $FILES; do for k in FROM TO; do v="$(pin PIN_${k}_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_${k}_$(base "$f").txt is missing in the kit"; done; done
for f in $READERS; do v="$(pin PIN_READ_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base "$f").txt is missing in the kit"; done
for f in make_s559.py s559_ar_block.txt walk_s559.py s551_lines_s559.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
[ -f "$W557" ] && [ -f "$W555" ] && [ -f "$W551" ] || die "the S557 / S555 / S551 walks (regression) are not beside this kit"
for f in $FILES $READERS; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    $APP ok; database and uploads read from the service (not shown)"

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (the five files at the kit's pins)"
  echo "  PINS (read back): $(for f in $FILES; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)"
  exit 0
fi
for f in $FILES; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; rebuild S559 on the new bytes"
  echo "    $f ${P:0:8} ok"
done
for f in $READERS; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f (read only) is ${L:0:8}, not the pinned ${P:0:8} -- the walk was proven on other bytes"
  echo "    $f ${P:0:8} ok (read only)"
done

WORK="$(mktemp -d /tmp/s559_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"
trap 'rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.tmp"; done' EXIT

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built" "$WORK/am" "$WORK/noam"
for f in $FILES $READERS; do cp "$APP/$f" "$WORK/live_in/"; done
"$PY" -B "$HERE/make_s559.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
for f in $READERS; do cp "$APP/$f" "$WORK/built/"; done
for f in $FILES; do
  B="$(md5 "$WORK/built/$f")"; P="$(pin PIN_TO_$(base "$f").txt)"
  [ "$B" = "$P" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"
done
cp "$WORK/built/asset_machine.py" "$WORK/am/"
for f in asset_register.py sorting_desk.py clinic_papers.py scanner_widget.js $READERS; do cp "$WORK/built/$f" "$WORK/noam/"; done

log "compile on both pythons"
mkdir -p "$WORK/cc"; for f in $PYFILES; do cp "$WORK/built/$f" "$WORK/cc/"; done
( cd "$WORK/cc" && "$PY" -m py_compile $PYFILES ) || die "a built file does not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $PYFILES ) || die "a built file does not compile on $PYV"; echo "    compiles on $PY and $PYV"; else echo "    compiles on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walk on a scratch copy of the database (made-up rows; nothing sent anywhere) -- the baseline, the walk, the control, the S557, S555 and S551 walks"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$WORK/snap.db" || die "the scratch copy of the database failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s559.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w0" --shared "$SHARED" --dump "$WORK/baseline.json" > "$WORK/base.txt" 2>&1 ) || { tail -3 "$WORK/base.txt"; die "the baseline of reception's pages could not be taken on the live files"; }
( cd "$WORK" && "$PY" -B "$HERE/walk_s559.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w1" --shared "$SHARED" --baseline "$WORK/baseline.json" --from-widget "$WORK/live_in/scanner_widget.js" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E '^SIZES' "$WORK/walk.txt" | head -1 | sed 's/^/    /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s559.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w2" --shared "$SHARED" --baseline "$WORK/baseline.json" --from-widget "$WORK/live_in/scanner_widget.js" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | tail -1 | sed 's/^/    /'
# S557's walk: its unchanged-pages baseline from the S559 build WITHOUT asset_machine.py (S559 changes every page's menu by
# design; K1 then proves a manager's machine page with machine.on off is that page exactly, K2 the intake)
( cd "$WORK" && "$PY" -B "$W557" "$WORK/noam" "$WORK/snap.db" --work "$WORK/w3" --shared "$SHARED" --dump "$WORK/b557.json" > "$WORK/s557base.txt" 2>&1 ) || { tail -3 "$WORK/s557base.txt"; die "the S557 walk's baseline could not be taken"; }
( cd "$WORK" && "$PY" -B "$W557" "$WORK/built" "$WORK/snap.db" --work "$WORK/w4" --shared "$SHARED" --baseline "$WORK/b557.json" > "$WORK/s557.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s557.txt"; die "the S557 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s557.txt" | tail -1 | sed 's/^/    S557 walk on the new files: /'
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$W555" "$WORK/built" "$WORK/snap.db" --work "$WORK/w5" --shared "$SHARED" > "$WORK/s555.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s555.txt"; die "the S555 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s555.txt" | tail -1 | sed 's/^/    S555 walk on the new files: /'
"$PY" -B "$HERE/s551_lines_s559.py" "$W551" "$WORK/walk_s551_s559.py" > "$WORK/s551lines.txt" 2>&1 || { cat "$WORK/s551lines.txt"; die "the S551 walk's three agreed lines were not each found exactly once"; }
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$WORK/walk_s551_s559.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w6" --shared "$SHARED" > "$WORK/s551.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s551.txt"; die "the S551 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s551.txt" | tail -1 | sed 's/^/    S551 walk (its date line, and the two lines S559 changes on purpose) on the new files: /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run)"; exit 0; fi

log "backups beside the live files, and the database by the backup API (no data step: a safety copy only)"
for f in $FILES; do
  P="$(pin PIN_FROM_$(base "$f").txt)"; cp -p "$APP/$f" "$APP/$f.bak_S559_${P:0:8}" || die "backup of $f failed"
done
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S559_$STAMP" || die "database backup failed"
echo "    the five files .bak_S559_<from8> . $(basename "$DB").bak_S559_$STAMP"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING the five files from their backups"
  for f in $FILES; do
    P="$(pin PIN_FROM_$(base "$f").txt)"
    cp -p "$APP/$f.bak_S559_${P:0:8}" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"
  done
  eval "$RESTART" || true
  for f in $FILES; do
    [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || { echo "RESTORE FAILED ($f) -- run the UNDO line in the README"; exit 2; }
  done
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE APP DOES NOT ANSWER (healthz ${RH:-nothing}) -- the scan app is DOWN: tell Claude now"; exit 2; }
  echo "    files back at $(for f in $FILES; do printf '%s ' "$(md5 "$APP/$f" | cut -c1-8)"; done)(the FROM pins); healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays -- nothing in the database was changed)"
  exit 1
}

log "place (the modules first, the widget, the app's own file last), and read the md5 back"
for f in $FILES; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || restore; done
echo "    placed: the five files at the kit's pins"

log "restart $SERVICE only, then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S559_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
DESK=""; for i in $(seq 1 "$TRIES"); do DESK="$(hc "${HEALTH%/healthz}/desk")"; [ "$DESK" = "302" ] && break; sleep 2; done
if [ "$DESK" = "302" ]; then
  echo "    /desk answers 302 (the login gate -- expected, not a failure): the app is up and gated"
else
  echo "    /desk answered ${DESK:-nothing}, not 302: the desk did not mount, or its login gate is open"; restore
fi
WJ="$(curl -s --max-time 10 "${HEALTH%/healthz}/scan/widget.js" 2>/dev/null | grep -c 'S559.1' || true)"
if [ "${WJ:-0}" -ge 1 ]; then echo "    the served scanner widget carries S559.1 (phones take it the next time the intake opens)"
else echo "    the served widget does not carry S559.1"; restore; fi

echo
echo "$KIT: DONE."
echo "  PINS (read back): $(for f in $FILES; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)"
echo "  WHAT HIS PAGES NOW SHOW: one menu on every page of his and on the desk's pages -- Sorting desk (N) . The month . Bills"
echo "  awaited (N) . Implant ledger . Machines . Renewals . All papers . Vendors . Admin. The scan app's home opens with"
echo "  'N papers waiting -- Open the sorting desk'. Every clinic paper's row (All papers, the papers list, Bills awaited, the"
echo "  ledger, The month, a machine's paper) opens the desk on that paper; a pharmacy paper keeps its old page. The old bill"
echo "  page shows the scan at the top, 'Open on the sorting desk', and Waiting / Filed / Accepted / Set aside. Shavez sees the"
echo "  desk items once 'Sorting desk for Shavez' is ON. Reception's scan screen: Save while adjusting now saves ONE paper."
echo "  UNDO (one line): $(for f in $FILES; do P="$(pin PIN_FROM_$(base "$f").txt)"; printf '\\cp -p %s %s && ' "$APP/$f.bak_S559_${P:0:8}" "$APP/$f"; done)systemctl restart $SERVICE"
exit 0
