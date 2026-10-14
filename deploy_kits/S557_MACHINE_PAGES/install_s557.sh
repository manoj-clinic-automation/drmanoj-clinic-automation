#!/bin/bash
# install_s557.sh -- S557_MACHINE_PAGES: the machine pages (the cover line and the totals; Parts, Cover history and Spends, each
# row with its scanned paper; one reminder per live cover / part on the renewals list; a new machine from a Clinic-equipment
# paper), the switch machine.on (installed OFF for Shavez), one word per lane on the owner's and managers' pages, a Claude
# amount that is not a number ignored on the desk. Additive database change: asset_part, asset_cover, service_logs.bill_id.
# BUILD_NORM_v1 s3 order (S555's shape): gates -> FROM pins (and the readers it depends on) -> rebuild from the live bytes ->
# TO pins -> compile (both pythons) -> baseline + walk + control + the S555 and S551 walks on a scratch copy (DRY=1 stops
# here) -> backups (files, and the database by the backup API) -> place -> md5 read-back -> data step (asset_machine.ensure:
# the tables, the column, the reminders' heal) -> restart the named service only -> /healthz 200 and /desk 302 (the login
# gate; 302 ONLY) -> machine.on left absent -> what his pages now show -> undo line. A failure after placing restores.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S557_MACHINE_PAGES/install_s557.sh
set -u
KIT="S557_MACHINE_PAGES"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KITS="${S557_KITS_DIR:-$(cd "$HERE/.." && pwd)}"
APP="${S557_APP_DIR:-/root/assetapp}"
SERVICE="${S557_SERVICE:-assetapp}"
HEALTH="${S557_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S557_PYTHON:-python3}"
PYV="${S557_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S557_RESTART_CMD:-systemctl restart $SERVICE}"
SHARED="${S557_SHARED_DIR:-/root/shared}"
TRIES="${S557_HEALTH_TRIES:-20}"
EDITED="sorting_desk.py asset_register.py"                         # rebuilt from the live bytes
FILES="asset_machine.py sorting_desk.py asset_register.py"         # placed in this order: the new module first, the app's own file last
READERS="clinic_papers.py claude_reader.py claude_reread.py"        # read only; pinned (the walk imports them)
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
if [ -z "${S557_DB:-}" ] || [ -z "${S557_UPLOADS:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  UP0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_UPLOADS=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S557_DB:-${DB0:-$APP/assets.db}}"
UP="${S557_UPLOADS:-${UP0:-$APP/uploads}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
W555="$KITS/S555_DESK_CORRECTIONS/walk_s555.py"
W551="$KITS/S551_SORTING_DESK/walk_s551.py"

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for f in $EDITED; do for k in FROM TO; do v="$(pin PIN_${k}_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_${k}_$(base "$f").txt is missing in the kit"; done; done
v="$(pin PIN_TO_asset_machine.txt)"; [ ${#v} -eq 32 ] || die "PIN_TO_asset_machine.txt is missing in the kit"
for f in $READERS; do v="$(pin PIN_READ_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base "$f").txt is missing in the kit"; done
for f in make_s557.py walk_s557.py asset_machine.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
[ "$(md5 "$HERE/asset_machine.py")" = "$(pin PIN_TO_asset_machine.txt)" ] || die "the kit's asset_machine.py is not the pinned one"
[ -f "$W555" ] && [ -f "$W551" ] || die "the S555 / S551 walks (regression) are not beside this kit"
for f in $EDITED $READERS; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    $APP ok; database and uploads read from the service (not shown)"

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in $FILES; do [ -f "$APP/$f" ] && [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (the three files at the kit's pins)"
  echo "  PINS (read back): asset_machine.py $(md5 "$APP/asset_machine.py") . sorting_desk.py $(md5 "$APP/sorting_desk.py") . asset_register.py $(md5 "$APP/asset_register.py")"
  exit 0
fi
for f in $EDITED; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; rebuild S557 on the new bytes"
  echo "    $f ${P:0:8} ok"
done
[ -e "$APP/asset_machine.py" ] && die "an asset_machine.py is already in $APP and it is not this kit's -- nothing placed"
for f in $READERS; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f (read only) is ${L:0:8}, not the pinned ${P:0:8} -- the walk was proven on other bytes"
  echo "    $f ${P:0:8} ok (read only)"
done

WORK="$(mktemp -d /tmp/s557_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"
trap 'rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.tmp"; done' EXIT

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built" "$WORK/am"
for f in $EDITED $READERS; do cp "$APP/$f" "$WORK/live_in/"; done
"$PY" -B "$HERE/make_s557.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
for f in $READERS; do cp "$APP/$f" "$WORK/built/"; done
cp "$WORK/built/asset_machine.py" "$WORK/am/"
for f in $FILES; do
  B="$(md5 "$WORK/built/$f")"; P="$(pin PIN_TO_$(base "$f").txt)"
  [ "$B" = "$P" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"
done

log "compile on both pythons"
mkdir -p "$WORK/cc"; for f in $FILES; do cp "$WORK/built/$f" "$WORK/cc/"; done
( cd "$WORK/cc" && "$PY" -m py_compile $FILES ) || die "a built file does not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $FILES ) || die "a built file does not compile on $PYV"; echo "    compiles on $PY and $PYV"; else echo "    compiles on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walk on a scratch copy of the database (made-up rows; nothing sent anywhere) -- the baseline, the walk, the control, the S555 and S551 walks"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$WORK/snap.db" || die "the scratch copy of the database failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s557.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w0" --shared "$SHARED" --dump "$WORK/baseline.json" > "$WORK/base.txt" 2>&1 ) || { tail -3 "$WORK/base.txt"; die "the baseline of the unchanged pages could not be taken on the live files"; }
( cd "$WORK" && "$PY" -B "$HERE/walk_s557.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w1" --shared "$SHARED" --baseline "$WORK/baseline.json" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E '^SIZES' "$WORK/walk.txt" | head -1 | sed 's/^/    /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s557.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w2" --shared "$SHARED" --baseline "$WORK/baseline.json" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | tail -1 | sed 's/^/    /'
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$W555" "$WORK/built" "$WORK/snap.db" --work "$WORK/w3" --shared "$SHARED" > "$WORK/s555.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s555.txt"; die "the S555 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s555.txt" | tail -1 | sed 's/^/    S555 walk on the new files: /'
sed 's/checked up to 15-Jun-2031/checked up to 15-06-2031/' "$W551" > "$WORK/walk_s551_ddmm.py"
[ "$(diff "$W551" "$WORK/walk_s551_ddmm.py" | grep -c '^>')" = "1" ] || die "the S551 walk's one date line (S555's agreed form) was not found exactly once"
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$WORK/walk_s551_ddmm.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w4" --shared "$SHARED" > "$WORK/s551.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s551.txt"; die "the S551 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s551.txt" | tail -1 | sed 's/^/    S551 walk (its one date line in dd-mm-yyyy, S555) on the new files: /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run)"; exit 0; fi

log "backups beside the live files, and the database by the backup API (before the additive data step)"
for f in $EDITED; do
  P="$(pin PIN_FROM_$(base "$f").txt)"; cp -p "$APP/$f" "$APP/$f.bak_S557_${P:0:8}" || die "backup of $f failed"
done
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S557_$STAMP" || die "database backup failed"
echo "    sorting_desk.py / asset_register.py .bak_S557_<from8> . $(basename "$DB").bak_S557_$STAMP"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING the two files from their backups; the new module set aside"
  for f in $EDITED; do
    P="$(pin PIN_FROM_$(base "$f").txt)"
    cp -p "$APP/$f.bak_S557_${P:0:8}" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"
  done
  [ -e "$APP/asset_machine.py" ] && mv -f "$APP/asset_machine.py" "$APP/asset_machine.py.notinstalled_S557_$STAMP"
  eval "$RESTART" || true
  for f in $EDITED; do
    [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || { echo "RESTORE FAILED ($f) -- run the UNDO line in the README"; exit 2; }
  done
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE APP DOES NOT ANSWER (healthz ${RH:-nothing}) -- the scan app is DOWN: tell Claude now"; exit 2; }
  echo "    files back at $(for f in $EDITED; do printf '%s ' "$(md5 "$APP/$f" | cut -c1-8)"; done)(the FROM pins); asset_machine.py set aside; healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays; the two new tables and the column are additive and unused)"
  exit 1
}

log "place (the new module first, then the desk, then the app), and read the md5 back"
for f in $FILES; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || restore; done
echo "    placed: the three files at the kit's pins"

log "data step: asset_machine.ensure -- asset_part, asset_cover, service_logs.bill_id (additive), then the reminders' heal"
( cd "$WORK" && "$PY" -B "$APP/asset_machine.py" --ensure "$DB" ) || { echo "    the data step failed"; restore; }

log "restart $SERVICE only, then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S557_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
DESK=""; for i in $(seq 1 "$TRIES"); do DESK="$(hc "${HEALTH%/healthz}/desk")"; [ "$DESK" = "302" ] && break; sleep 2; done
if [ "$DESK" = "302" ]; then
  echo "    /desk answers 302 (the login gate -- expected, not a failure): the app is up and gated"
else
  echo "    /desk answered ${DESK:-nothing}, not 302: the desk did not mount, or its login gate is open"; restore
fi
MON="$("$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); r=c.execute(\"SELECT value FROM settings WHERE key='machine.on'\").fetchone(); print(r[0] if r else 'absent')" "$DB" 2>/dev/null)"
echo "    machine.on: ${MON:-absent} (left as it was; absent = OFF for Shavez)"

echo
echo "$KIT: DONE."
echo "  PINS (read back): asset_machine.py $(md5 "$APP/asset_machine.py") . sorting_desk.py $(md5 "$APP/sorting_desk.py") . asset_register.py $(md5 "$APP/asset_register.py")"
echo "  WHAT HIS PAGES NOW SHOW: each machine's page (Scan app & assets -> Assets -> a machine) opens with one cover line"
echo "  ('Covered: AMC by ... till dd-mm-yyyy', amber in its last 30 days, red once lapsed, or 'No cover') and one line of totals;"
echo "  under the details three folds -- Parts, Cover history, Spends -- each row with its scanned paper (B-____). Every live"
echo "  cover and part warranty puts one reminder on Renewals. A Clinic-equipment paper offers '+ asset record' (a new machine,"
echo "  pre-filled from the paper). Lanes read in one word on his and Shavez's pages. Shavez sees none of the new machine parts"
echo "  until the owner turns on 'Machine pages for Shavez' on the Switches card."
echo "  UNDO (one line): $(for f in $EDITED; do P="$(pin PIN_FROM_$(base "$f").txt)"; printf '\\cp -p %s %s && ' "$APP/$f.bak_S557_${P:0:8}" "$APP/$f"; done)mv $APP/asset_machine.py $APP/asset_machine.py.undone_S557 && systemctl restart $SERVICE"
exit 0
