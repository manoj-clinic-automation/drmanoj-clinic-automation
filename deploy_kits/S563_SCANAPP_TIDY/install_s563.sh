#!/bin/bash
# install_s563.sh -- S563_SCANAPP_TIDY (D646 PLANNED line, board v438): the scan app's last tidy round. F-902 "Already set aside
# on dd-mm-yyyy -- Restore?" on the desk (one shared restore, never straight back to accepted); the old Bills awaited page filters
# a patient's / Personal challan as the desk does; the owner's Delete voids the payment a paper proves and clears a machine's
# link; a statement pays the invoices with a total first; one machine per paper under a lock; the stamp box refuses a copy / a
# page; an old AMC whose own renewal date is past reads lapsed; receipt / statement words never matched on item names; the
# intake widget's Adjust stage after a delete; three comments; clinic_papers.py consolidated (no served byte changes).
# Files: /root/assetapp/sorting_desk.py, clinic_papers.py, asset_machine.py, scanner_widget.js, asset_register.py (the scan app
# only). NO data step, NO new column. Only assetapp restarts (the widget is a static file; clinic-finance is not touched).
# BUILD_NORM_v1 s3 order (S560's shape): gates -> the build lock -> FROM pins (and the read-only pins) -> rebuild from the live
# bytes -> TO pins -> compile (both pythons) -> the walk (with item 12's byte-identical fetch) + control, the S560 (+ pack),
# S559, S557, S555, S551 and S548 walks on a scratch copy (DRY=1 stops here) -> backups (files; the database by the backup
# API) -> place -> md5 read-back -> restart assetapp -> /healthz 200, /desk 302 (302 ONLY), the served widget carries S563 ->
# what his pages now show -> undo line -> the builders' old scratch under ${S563_SCRATCH_ROOT:-/tmp} (item 13).
# A failure after placing restores all five files and restarts assetapp.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S563_SCANAPP_TIDY/install_s563.sh
set -u
KIT="S563_SCANAPP_TIDY"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KITS="${S563_KITS_DIR:-$(cd "$HERE/.." && pwd)}"
APP="${S563_APP_DIR:-/root/assetapp}"
FIN="${S563_FIN_DIR:-/root/finance}"
SERVICE="${S563_SERVICE:-assetapp}"
HEALTH="${S563_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S563_PYTHON:-python3}"
PYV="${S563_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S563_RESTART_CMD:-systemctl restart $SERVICE}"
SHARED="${S563_SHARED_DIR:-/root/shared}"
LOCK="${S563_LOCK:-/root/deploy/.claude_code_build.lock}"
TRIES="${S563_HEALTH_TRIES:-20}"
SCRATCH_ROOT="${S563_SCRATCH_ROOT:-/tmp}"
W559FROM="${S563_W559_FROM:-$APP/scanner_widget.js.bak_S559_1143c77b}"     # the widget before S559 (S559's walk J1 compares against it)
PK_BEFORE="${S563_PACK_BEFORE:-$FIN/packs.py.bak_S560_d86d351a}"            # packs.py before S560 (S560's pack walk P8 compares against it)
FILES="sorting_desk.py clinic_papers.py asset_machine.py scanner_widget.js asset_register.py"   # placed in this order, the app's own file last
PYFILES="sorting_desk.py clinic_papers.py asset_machine.py asset_register.py"
READERS="claude_reader.py claude_reread.py"                                   # read only; pinned (the walks import them)
OLD_SCRATCH="s560fix1a s560fix1b s560fix1probe s560fix2a s560fix2_pins.sh s554kit s554probe"   # item 13
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
if [ -z "${S563_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S563_DB:-${DB0:-$APP/assets.db}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
W560="$KITS/S560_RECEIPTS_STATEMENTS/walk_s560.py"
W560P="$KITS/S560_RECEIPTS_STATEMENTS/walk_s560_pack.py"
W559="$KITS/S559_ONE_ROAD/walk_s559.py"
L559="$KITS/S559_ONE_ROAD/s551_lines_s559.py"
W557="$KITS/S557_MACHINE_PAGES/walk_s557.py"
W555="$KITS/S555_DESK_CORRECTIONS/walk_s555.py"
W551="$KITS/S551_SORTING_DESK/walk_s551.py"
W548="$KITS/S548_PACK_BHAWNA_FILE/walk_s548.py"
HAVE_LOCK=0
WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.tmp"; done; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap cleanup EXIT

# item 13: the builders' old scratch -- each name only if it holds no database / JSON file (symlinks never followed); else left, named
scratch_tidy(){
  local n p hit
  for n in $OLD_SCRATCH; do
    p="$SCRATCH_ROOT/$n"
    if [ -L "$p" ]; then echo "    left $p: a symlink (never followed)"; continue; fi
    [ -e "$p" ] || { echo "    $p: not there"; continue; }
    hit="$(find -P "$p" \( -name '*.db' -o -name '*.sqlite' -o -name '*.db-wal' -o -name '*.db-shm' -o -name '*.json' \) -print -quit 2>/dev/null)"
    if [ -n "$hit" ]; then echo "    left $p: it holds a database / JSON file ($(basename "$hit"))"; continue; fi
    if [ -n "$(find -P "$p" -type l -print -quit 2>/dev/null)" ]; then echo "    left $p: it holds a symlink (never followed)"; continue; fi
    rm -rf --one-file-system "$p" && echo "    removed $p" || echo "    left $p: could not be removed"
  done
}

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for f in $FILES; do for k in FROM TO; do v="$(pin PIN_${k}_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_${k}_$(base "$f").txt is missing in the kit"; done; done
for f in $READERS packs.py; do v="$(pin PIN_READ_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base "$f").txt is missing in the kit"; done
for p in PIN_READ_widget_before_s559.txt PIN_READ_packs_before_s560.txt PIN_ITEM3_clinic_papers.txt; do v="$(pin $p)"; [ ${#v} -eq 32 ] || die "$p is missing in the kit"; done
for f in make_s563.py walk_s563.py fetch_s563.py lines_s563.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
for w in "$W560" "$W560P" "$W559" "$L559" "$W557" "$W555" "$W551" "$W548"; do [ -f "$w" ] || die "the earlier walk $w (regression) is not beside this kit"; done
for f in $FILES $READERS; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$FIN/packs.py" ] || die "$FIN/packs.py missing (read only: the pack walks)"
[ -f "$W559FROM" ] && [ "$(md5 "$W559FROM")" = "$(pin PIN_READ_widget_before_s559.txt)" ] || die "the widget before S559 (S559's walk compares against it) is not at $W559FROM"
[ -f "$PK_BEFORE" ] && [ "$(md5 "$PK_BEFORE")" = "$(pin PIN_READ_packs_before_s560.txt)" ] || die "packs.py before S560 (S560's pack walk compares against it) is not at $PK_BEFORE"
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    $APP ok; the database read from the service (not shown)"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (the five files at the kit's pins)"
  echo "  PINS (read back): $(for f in $FILES; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)"
  exit 0
fi
for f in $FILES; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; rebuild S563 on the new bytes"
  echo "    $f ${P:0:8} ok"
done
for f in $READERS; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f (read only) is ${L:0:8}, not the pinned ${P:0:8} -- the walk was proven on other bytes"
  echo "    $f ${P:0:8} ok (read only)"
done
L="$(md5 "$FIN/packs.py")"; P="$(pin PIN_READ_packs.txt)"
[ "$L" = "$P" ] || die "packs.py (the parent's, read only) is ${L:0:8}, not the pinned ${P:0:8} -- the pack walks were proven on other bytes"
echo "    packs.py ${P:0:8} ok (the parent's, read only, not touched)"

WORK="$(mktemp -d /tmp/s563_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built" "$WORK/cp3" "$WORK/am" "$WORK/noam"
for f in $FILES $READERS; do cp "$APP/$f" "$WORK/live_in/"; done
"$PY" -B "$HERE/make_s563.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
sed 's/^/    /' "$WORK/make.txt"
"$PY" -B "$HERE/make_s563.py" "$WORK/live_in" "$WORK/cp3" --cp-item3-only > "$WORK/make3.txt" 2>&1 || { cat "$WORK/make3.txt"; die "the builder refused (item 3 only)"; }
for f in $READERS; do cp "$APP/$f" "$WORK/built/"; done
for f in $FILES; do
  B="$(md5 "$WORK/built/$f")"; P="$(pin PIN_TO_$(base "$f").txt)"
  [ "$B" = "$P" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"
done
B="$(md5 "$WORK/cp3/clinic_papers.py")"; P="$(pin PIN_ITEM3_clinic_papers.txt)"
[ "$B" = "$P" ] || die "clinic_papers.py with item 3 only is ${B:0:8}, the kit says ${P:0:8}"; echo "    clinic_papers.py with item 3 only (the tidy's comparison) ${B:0:8} = the kit's pin"
cp "$WORK/built/asset_machine.py" "$WORK/am/"
for f in sorting_desk.py clinic_papers.py asset_register.py scanner_widget.js $READERS; do cp "$WORK/built/$f" "$WORK/noam/"; done

log "compile on both pythons"
mkdir -p "$WORK/cc"; for f in $PYFILES; do cp "$WORK/built/$f" "$WORK/cc/"; done
( cd "$WORK/cc" && "$PY" -m py_compile $PYFILES ) || die "a built file does not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $PYFILES ) || die "a built file does not compile on $PYV"; echo "    compiles on $PY and $PYV"; else echo "    compiles on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walks on a scratch copy of the database (made-up rows; nothing sent anywhere) -- S563's walk (and item 12's fetch) and control; the S560 (+ pack), S548, S559, S557, S555 and S551 walks"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$WORK/snap.db" || die "the scratch copy of the database failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s563.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w1" --shared "$SHARED" --tidy-from "$WORK/cp3" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt"; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E '^TIDY' "$WORK/walk.txt" | sed 's/^/    /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s563.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w2" --shared "$SHARED" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | tail -1 | sed 's/^/    /'
"$PY" -B "$HERE/lines_s563.py" s560 "$W560" "$WORK/walk_s560_s563.py" > "$WORK/l560.txt" 2>&1 || { cat "$WORK/l560.txt"; die "the S560 walk's line S563 changes was not found exactly once"; }
( cd "$WORK" && "$PY" -B "$WORK/walk_s560_s563.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w3" --shared "$SHARED" > "$WORK/s560.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s560.txt"; die "the S560 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s560.txt" | tail -1 | sed 's/^/    S560 walk (its K2 line in S563'"'"'s form) on the new files: /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$W560P" "$FIN/packs.py" "$FIN" --before "$PK_BEFORE" > "$WORK/pack.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/pack.txt"; die "the S560 pack walk is RED"; }
grep -E 'pack checks' "$WORK/pack.txt" | tail -1 | sed 's/^/    S560 pack walk (packs.py unchanged): /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$W548" "$FIN/packs.py" "$FIN" > "$WORK/s548.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s548.txt"; die "the S548 pack walk is RED"; }
grep -E 'checks' "$WORK/s548.txt" | tail -1 | sed 's/^/    S548 pack walk: /'
"$PY" -B "$HERE/lines_s563.py" s559 "$W559" "$WORK/walk_s559_s563.py" > "$WORK/l559.txt" 2>&1 || { cat "$WORK/l559.txt"; die "the S559 walk's lines S563 changes were not each found exactly once"; }
( cd "$WORK" && "$PY" -B "$W559" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w4" --shared "$SHARED" --dump "$WORK/b559.json" > "$WORK/s559base.txt" 2>&1 ) || { tail -3 "$WORK/s559base.txt"; die "the S559 walk's baseline could not be taken on the live files"; }
( cd "$WORK" && "$PY" -B "$WORK/walk_s559_s563.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w5" --shared "$SHARED" --baseline "$WORK/b559.json" --from-widget "$W559FROM" > "$WORK/s559.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s559.txt"; die "the S559 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s559.txt" | tail -1 | sed 's/^/    S559 walk (its J1 \/ J3 lines in S563'"'"'s form) on the new files: /'
( cd "$WORK" && "$PY" -B "$W557" "$WORK/noam" "$WORK/snap.db" --work "$WORK/w6" --shared "$SHARED" --dump "$WORK/b557.json" > "$WORK/s557base.txt" 2>&1 ) || { tail -3 "$WORK/s557base.txt"; die "the S557 walk's baseline could not be taken"; }
( cd "$WORK" && "$PY" -B "$W557" "$WORK/built" "$WORK/snap.db" --work "$WORK/w7" --shared "$SHARED" --baseline "$WORK/b557.json" > "$WORK/s557.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s557.txt"; die "the S557 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s557.txt" | tail -1 | sed 's/^/    S557 walk on the new files: /'
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$W555" "$WORK/built" "$WORK/snap.db" --work "$WORK/w8" --shared "$SHARED" > "$WORK/s555.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s555.txt"; die "the S555 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s555.txt" | tail -1 | sed 's/^/    S555 walk on the new files: /'
"$PY" -B "$L559" "$W551" "$WORK/walk_s551_s559.py" > "$WORK/s551lines.txt" 2>&1 || { cat "$WORK/s551lines.txt"; die "the S551 walk's three agreed lines (S559's) were not each found exactly once"; }
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$WORK/walk_s551_s559.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w9" --shared "$SHARED" > "$WORK/s551.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s551.txt"; die "the S551 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s551.txt" | tail -1 | sed 's/^/    S551 walk (S559'"'"'s three agreed lines) on the new files: /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run)"; exit 0; fi

log "backups beside the live files, and the database by the backup API (no data step follows)"
for f in $FILES; do
  P="$(pin PIN_FROM_$(base "$f").txt)"; cp -p "$APP/$f" "$APP/$f.bak_S563_${P:0:8}" || die "backup of $f failed"
done
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S563_$STAMP" || die "database backup failed"
echo "    the five files .bak_S563_<from8> . $(basename "$DB").bak_S563_$STAMP"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING the five files from their backups"
  for f in $FILES; do
    P="$(pin PIN_FROM_$(base "$f").txt)"
    cp -p "$APP/$f.bak_S563_${P:0:8}" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"
  done
  eval "$RESTART" || true
  for f in $FILES; do
    [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || { echo "RESTORE FAILED ($f) -- run the UNDO line in the README"; exit 2; }
  done
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE SCAN APP DOES NOT ANSWER (${RH:-nothing}) -- tell Claude now"; exit 2; }
  echo "    files back at $(for f in $FILES; do printf '%s ' "$(md5 "$APP/$f" | cut -c1-8)"; done)(the FROM pins); healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays -- no data step ran, nothing in the database was changed by the kit)"
  exit 1
}

log "place (the modules first, the widget, the app's own file last), and read the md5 back"
for f in $FILES; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || restore; done
echo "    placed: the five files at the kit's pins"

log "restart $SERVICE (only), then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S563_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
DESK=""; for i in $(seq 1 "$TRIES"); do DESK="$(hc "${HEALTH%/healthz}/desk")"; [ "$DESK" = "302" ] && break; sleep 2; done
if [ "$DESK" = "302" ]; then
  echo "    /desk answers 302 (the login gate -- expected, not a failure): the app is up and gated"
else
  echo "    /desk answered ${DESK:-nothing}, not 302: the desk did not mount, or its login gate is open"; restore
fi
WJ="$(curl -s --max-time 10 "${HEALTH%/healthz}/scan/widget.js" 2>/dev/null | grep -c 'S563: a late Adjust picture' || true)"
if [ "${WJ:-0}" -ge 1 ]; then echo "    the served scanner widget carries S563's correction (phones take it the next time the intake opens: its ?v= is the file's time)"
else echo "    the served widget does not carry S563's correction"; restore; fi

echo
echo "$KIT: DONE."
echo "  PINS (read back): $(for f in $FILES; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)"
echo "  WHAT HIS PAGES NOW SHOW: on the sorting desk a paper already set aside reads 'Already set aside on dd-mm-yyyy — Restore?'"
echo "  with one Restore button; Restore puts it back to be sorted (never straight to accepted -- its Save accepts it as usual)."
echo "  Bills awaited (the old page) never lists a patient's challan, and a Personal one only for him. Deleting a receipt makes"
echo "  the bill it paid read unpaid again. A statement pays the invoices that have a total first. A machine is made once per"
echo "  paper; the stamp box sends a copy / a page to the real paper; an old AMC past its own renewal date reads lapsed (red)."
echo "  Reception's intake is as before, except the Adjust stage after a page is deleted (the right page, the right number)."
echo "  UNDO (one line): $(for f in $FILES; do P="$(pin PIN_FROM_$(base "$f").txt)"; printf '\\cp -p %s %s && ' "$APP/$f.bak_S563_${P:0:8}" "$APP/$f"; done)systemctl restart $SERVICE"
log "the builders' old scratch under $SCRATCH_ROOT (item 13)"
scratch_tidy
exit 0
