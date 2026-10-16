#!/bin/bash
# install_s571.sh -- S571_BATTERIES (D646 PLANNED line, board v455; the owner's rulings D730 (1)): Batteries.
# A list of battery places (batteries.py, the page "Batteries" in the scan app's menu after Machines): totals; four groups (Online
# UPS, Small UPS, Generator and inverters, Vehicles); one row per place with the battery now, fitted, warranty till, a status badge
# and "New battery fitted"; a place's history; the 15 seeded places (names only); "bill awaited" for a B.L. battery until its bill
# is linked -- on the sorting desk a B.L. Computers / Jasoria paper offers "Battery fitted at <place> on <date> — this bill?", one tap
# links it, the paper itself never changed; reminders computed when read, as one "Batteries" card on Renewals; a machine added in
# Machines after the install gets its place by itself; the switch batteries.on ("Batteries for Shavez", absent = OFF).
# Files: /root/assetapp/sorting_desk.py, asset_register.py, the NEW batteries.py (absent = its FROM state; present with other
# bytes = STOP). Read only, pinned: clinic_papers.py, stationery.py, asset_machine.py, scanner_widget.js, claude_reader.py,
# claude_reread.py and the parent's /root/finance/packs.py (S568's TO). Never touched: every finance and Sanjeevni file.
# Data step (batteries.py's own ensure, additive, idempotent, before placing): battery_place (+ the 15 seeded places by seed_key),
# battery_fit, battery_upkeep, two indexes and the one setting batteries.since -- no existing row changed.
# BUILD_NORM_v1 s3 order (S568's shape): gates -> the build lock -> FROM pins (and the read-only pins) -> rebuild from the live
# bytes -> TO pins -> compile (both pythons) -> S571's walk + control, then S568's, S566's, S563's (with its tidy fetch), S560's
# (+ pack), S548's, S559's, S557's, S555's and S551's walks on a scratch copy (DRY=1 stops here) -> backups (files; the database by
# the backup API) -> the data step -> place -> md5 read-back -> restart assetapp ONLY -> /healthz 200, /desk 302 and /batteries 302
# (302 ONLY) -> what his pages now show -> undo line. A failure after placing restores every file byte-identically (batteries.py
# removed: it was absent) and restarts assetapp.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S571_BATTERIES/install_s571.sh
set -u
KIT="S571_BATTERIES"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KITS="${S571_KITS_DIR:-$(cd "$HERE/.." && pwd)}"
APP="${S571_APP_DIR:-/root/assetapp}"
FIN="${S571_FIN_DIR:-/root/finance}"
SERVICE="${S571_SERVICE:-assetapp}"
HEALTH="${S571_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S571_PYTHON:-python3}"
PYV="${S571_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S571_RESTART_CMD:-systemctl restart $SERVICE}"
SHARED="${S571_SHARED_DIR:-/root/shared}"
LOCK="${S571_LOCK:-/root/deploy/.claude_code_build.lock}"
TRIES="${S571_HEALTH_TRIES:-20}"
W559FROM="${S571_W559_FROM:-$APP/scanner_widget.js.bak_S559_1143c77b}"     # the widget before S559 (S559's walk J1 compares against it)
PK_BEFORE="${S571_PACK_BEFORE:-$FIN/packs.py.bak_S560_d86d351a}"            # packs.py before S560 (S560's pack walk P8 compares against it)
PK_B568="${S571_PACK_BEFORE_S568:-$FIN/packs.py.bak_S568_048d2ad8}"         # packs.py before S568 (S568's walk I8 compares against it)
FILES="sorting_desk.py asset_register.py"                                    # placed in this order, the app's own file last
NEWF="batteries.py"                                                          # new: absent before; placed before asset_register.py
READONLY="clinic_papers.py stationery.py asset_machine.py scanner_widget.js claude_reader.py claude_reread.py"   # read only; pinned
PF="packs.py"                                                                # the parent's, read only (S568's TO); pinned, never placed
S563BAK="sorting_desk.py:a4623438 clinic_papers.py:88963eac asset_register.py:9daed9ea asset_machine.py:0caec41e scanner_widget.js:1128ac97"   # S563's own backups (its tidy fetch)
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
if [ -z "${S571_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S571_DB:-${DB0:-$APP/assets.db}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
K568="$KITS/S568_STATIONERY_STOCK"
K566="$KITS/S566_SCANAPP_LAST_FIXES"
K563="$KITS/S563_SCANAPP_TIDY"
W568="$K568/walk_s568.py"; M568="$K568/make_s568.py"; L568="$K568/lines_s568.py"
W566="$K566/walk_s566.py"; M566="$K566/make_s566.py"; L566="$K566/lines_s566.py"
W563="$K563/walk_s563.py"; M563="$K563/make_s563.py"; L563="$K563/lines_s563.py"
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
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES $NEWF; do rm -f "$APP/$f.tmp"; done; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap cleanup EXIT

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for f in $FILES; do for k in FROM TO; do v="$(pin PIN_${k}_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_${k}_$(base "$f").txt is missing in the kit"; done; done
v="$(pin PIN_TO_batteries.txt)"; [ ${#v} -eq 32 ] || die "PIN_TO_batteries.txt is missing in the kit"
for f in $READONLY $PF; do v="$(pin PIN_READ_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base "$f").txt is missing in the kit"; done
for p in PIN_READ_widget_before_s559.txt PIN_READ_packs_before_s560.txt PIN_READ_packs_before_s568.txt PIN_ITEM3_s563_clinic_papers.txt PIN_TIDY566_clinic_papers.txt PIN_TIDY568_clinic_papers.txt; do v="$(pin $p)"; [ ${#v} -eq 32 ] || die "$p is missing in the kit"; done
for f in make_s571.py walk_s571.py batteries.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
[ "$(md5 "$HERE/batteries.py")" = "$(pin PIN_TO_batteries.txt)" ] || die "the kit's batteries.py is not at its pin"
for w in "$W568" "$M568" "$L568" "$W566" "$M566" "$L566" "$W563" "$M563" "$L563" "$K563/fetch_s563.py" "$W560" "$W560P" "$W559" "$L559" "$W557" "$W555" "$W551" "$W548"; do [ -f "$w" ] || die "the earlier walk $w (regression) is not beside this kit"; done
for f in $FILES $READONLY; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
for p in $S563BAK; do f=${p%%:*}; h=${p##*:}; [ -f "$APP/$f.bak_S563_$h" ] && [ "$(md5 "$APP/$f.bak_S563_$h" | cut -c1-8)" = "$h" ] || die "S563's backup $f.bak_S563_$h (its tidy fetch is re-run from it) is not in $APP"; done
[ -f "$FIN/$PF" ] || die "$FIN/$PF missing"
[ -f "$W559FROM" ] && [ "$(md5 "$W559FROM")" = "$(pin PIN_READ_widget_before_s559.txt)" ] || die "the widget before S559 (S559's walk compares against it) is not at $W559FROM"
[ -f "$PK_BEFORE" ] && [ "$(md5 "$PK_BEFORE")" = "$(pin PIN_READ_packs_before_s560.txt)" ] || die "packs.py before S560 (S560's pack walk compares against it) is not at $PK_BEFORE"
[ -f "$PK_B568" ] && [ "$(md5 "$PK_B568")" = "$(pin PIN_READ_packs_before_s568.txt)" ] || die "packs.py before S568 (S568's walk I8 compares against it) is not at $PK_B568"
for f in scan_register.py purchase_app.py porders.py order_sheet.py; do [ -f "$FIN/$f" ] || die "the Sanjeevni reader $FIN/$f (read only: S568's walk runs its query) is missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    $APP and $FIN ok; the database read from the service (not shown)"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes must be the ones this kit was built on"
ALL_TO=1; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || ALL_TO=0; done
{ [ -f "$APP/$NEWF" ] && [ "$(md5 "$APP/$NEWF")" = "$(pin PIN_TO_batteries.txt)" ]; } || ALL_TO=0
if [ "$ALL_TO" = 1 ]; then
  echo "$KIT: ALREADY INSTALLED (the scan app's three files at the kit's pins)"
  echo "  PINS (read back): $(for f in $FILES $NEWF; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)"
  exit 0
fi
for f in $FILES; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; rebuild S571 on the new bytes"
  echo "    $f ${P:0:8} ok"
done
[ -e "$APP/$NEWF" ] && die "$NEWF is already in $APP ($(md5 "$APP/$NEWF" | cut -c1-8)) and the other files are not at the kit's pins -- it is not this kit's; stopped"
echo "    $NEWF absent (its FROM state) ok"
for f in $READONLY; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f (read only) is ${L:0:8}, not the pinned ${P:0:8} -- the walk was proven on other bytes"
  echo "    $f ${P:0:8} ok (read only, not touched)"
done
L="$(md5 "$FIN/$PF")"; P="$(pin PIN_READ_packs.txt)"
[ "$L" = "$P" ] || die "$PF (the parent's, read only) is ${L:0:8}, not the pinned ${P:0:8} (S568's TO) -- the earlier walks were proven on other bytes"
echo "    $PF ${P:0:8} ok (the parent's, read only, not touched)"
for f in scan_register.py purchase_app.py; do
  P="$(pin PIN_READ_$(base "$f").txt)"; L="$(md5 "$FIN/$f")"
  [ "$L" = "$P" ] && echo "    $f ${P:0:8} (Sanjeevni's, read only)" || echo "    $f is ${L:0:8}, not ${P:0:8} (Sanjeevni's, read only; S568's walk runs its query as it is now)"
done

WORK="$(mktemp -d /tmp/s571_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built" "$WORK/am" "$WORK/noam" "$WORK/s563from" "$WORK/s563cp3" "$WORK/tidy566" "$WORK/tidy" "$WORK/fin568"
for f in $FILES $READONLY; do cp "$APP/$f" "$WORK/live_in/"; done
"$PY" -B "$HERE/make_s571.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
sed 's/^/    /' "$WORK/make.txt"
for f in $READONLY; do cp "$APP/$f" "$WORK/built/"; done
for f in $FILES; do
  B="$(md5 "$WORK/built/$f")"; P="$(pin PIN_TO_$(base "$f").txt)"
  [ "$B" = "$P" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"
done
[ "$(md5 "$WORK/built/$NEWF")" = "$(pin PIN_TO_batteries.txt)" ] || die "batteries.py in the build is not at its pin"; echo "    $NEWF $(pin PIN_TO_batteries.txt | cut -c1-8) = the kit's pin (new)"
for p in $S563BAK; do f=${p%%:*}; h=${p##*:}; cp "$APP/$f.bak_S563_$h" "$WORK/s563from/$f"; done
"$PY" -B "$M563" "$WORK/s563from" "$WORK/s563cp3" --cp-item3-only > "$WORK/make563.txt" 2>&1 || { cat "$WORK/make563.txt"; die "S563's builder refused (item 3 only, from S563's own backups)"; }
[ "$(md5 "$WORK/s563cp3/clinic_papers.py")" = "$(pin PIN_ITEM3_s563_clinic_papers.txt)" ] || die "S563's item-3-only clinic_papers.py is not at its pin"
"$PY" -B "$M566" --cp-on "$WORK/s563cp3/clinic_papers.py" "$WORK/tidy566/clinic_papers.py" > "$WORK/maketidy566.txt" 2>&1 || { cat "$WORK/maketidy566.txt"; die "S566's clinic_papers edits did not apply to S563's item-3-only file"; }
[ "$(md5 "$WORK/tidy566/clinic_papers.py")" = "$(pin PIN_TIDY566_clinic_papers.txt)" ] || die "S566's tidy comparison file is not at its pin"
"$PY" -B "$M568" --cp-on "$WORK/tidy566/clinic_papers.py" "$WORK/tidy/clinic_papers.py" > "$WORK/maketidy.txt" 2>&1 || { cat "$WORK/maketidy.txt"; die "S568's clinic_papers edits did not apply to S566's tidy comparison file"; }
B="$(md5 "$WORK/tidy/clinic_papers.py")"; P="$(pin PIN_TIDY568_clinic_papers.txt)"
[ "$B" = "$P" ] || die "S568 on S566's tidy comparison file is ${B:0:8}, the kit says ${P:0:8}"
echo "    S563's tidy comparison rebuilt: S563 item 3 only -> S566's edits -> S568's edits = ${B:0:8} (S571 leaves clinic_papers.py as it is)"
cp "$WORK/built/asset_machine.py" "$WORK/am/"
for f in sorting_desk.py clinic_papers.py asset_register.py scanner_widget.js claude_reader.py claude_reread.py stationery.py batteries.py; do cp "$WORK/built/$f" "$WORK/noam/"; done
for f in scan_register.py purchase_app.py porders.py order_sheet.py; do cp "$FIN/$f" "$WORK/fin568/"; done
cp "$PK_B568" "$WORK/fin568/$PF"

log "compile on both pythons"
mkdir -p "$WORK/cc"; for f in $FILES $NEWF; do cp "$WORK/built/$f" "$WORK/cc/"; done
( cd "$WORK/cc" && "$PY" -m py_compile $FILES $NEWF ) || die "a built file does not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $FILES $NEWF ) || die "a built file does not compile on $PYV"; echo "    compiles on $PY and $PYV"; else echo "    compiles on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walks on a scratch copy of the database (made-up rows; nothing sent anywhere) -- S571's walk and control; S568's, S566's, S563's (and its tidy fetch), the S560 (+ pack), S548, S559, S557, S555 and S551 walks"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$WORK/snap.db" || die "the scratch copy of the database failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s571.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w1" --shared "$SHARED" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt" | cut -c1-400; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E 'counts' "$WORK/walk.txt" | cut -c1-400 | sed 's/^/      /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s571.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w2" --shared "$SHARED" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | sed 's/^/    /'
cp "$FIN/$PF" "$WORK/built/$PF"
( cd "$WORK" && "$PY" -B "$W568" "$WORK/built" "$WORK/snap.db" --work "$WORK/w12" --shared "$SHARED" --fin "$WORK/fin568" > "$WORK/s568.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s568.txt" | cut -c1-400; die "the S568 walk is RED on the built files"; }
rm -f "$WORK/built/$PF"
grep -E 'checks' "$WORK/s568.txt" | tail -1 | sed 's/^/    S568 walk on the new files (its I8 "before" = packs.py before S568, as when it was proven): /'
( cd "$WORK" && "$PY" -B "$W566" "$WORK/built" "$WORK/snap.db" --work "$WORK/w3" --shared "$SHARED" > "$WORK/s566.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s566.txt" | cut -c1-400; die "the S566 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s566.txt" | tail -1 | sed 's/^/    S566 walk on the new files: /'
"$PY" -B "$L566" s563 "$W563" "$WORK/walk_s563_s566.py" > "$WORK/l563.txt" 2>&1 || { cat "$WORK/l563.txt"; die "the S563 walk's line S566 changes was not found exactly once"; }
cp "$K563/fetch_s563.py" "$WORK/fetch_s563.py" || die "S563's fetch_s563.py (its tidy fetch) is not beside its walk"
( cd "$WORK" && "$PY" -B "$WORK/walk_s563_s566.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w4" --shared "$SHARED" --tidy-from "$WORK/tidy" > "$WORK/s563.txt" 2>&1 ) || { grep -E '^RED|checks|TIDY' "$WORK/s563.txt" | cut -c1-400; die "the S563 walk (or its tidy fetch) is RED on the built files"; }
grep -E 'checks' "$WORK/s563.txt" | tail -1 | sed 's/^/    S563 walk (its F4 line in S566'"'"'s form) on the new files: /'
grep -E '^TIDY' "$WORK/s563.txt" | sed 's/^/      /'
"$PY" -B "$L563" s560 "$W560" "$WORK/walk_s560_s563.py" > "$WORK/l560.txt" 2>&1 || { cat "$WORK/l560.txt"; die "the S560 walk's line (S563's form) was not found exactly once"; }
( cd "$WORK" && "$PY" -B "$WORK/walk_s560_s563.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w5" --shared "$SHARED" > "$WORK/s560.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s560.txt" | cut -c1-400; die "the S560 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s560.txt" | tail -1 | sed 's/^/    S560 walk (its K2 line in S563'"'"'s form) on the new files: /'
"$PY" -B "$L568" s560pack "$W560P" "$WORK/walk_s560_pack_s568.py" > "$WORK/l560p.txt" 2>&1 || { cat "$WORK/l560p.txt"; die "the S560 pack walk's lines in S568's form (P2, P8) were not each found exactly once"; }
( cd "$WORK" && HOME="$WORK" "$PY" -B "$WORK/walk_s560_pack_s568.py" "$FIN/$PF" "$FIN" --before "$PK_BEFORE" > "$WORK/pack.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/pack.txt"; die "the S560 pack walk is RED on the live packs.py"; }
grep -E 'pack checks' "$WORK/pack.txt" | tail -1 | sed 's/^/    S560 pack walk (P2 \/ P8 in S568'"'"'s form) on packs.py as it is (S571 does not touch it): /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$W548" "$FIN/$PF" "$FIN" > "$WORK/s548.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s548.txt"; die "the S548 pack walk is RED"; }
grep -E 'checks' "$WORK/s548.txt" | tail -1 | sed 's/^/    S548 pack walk: /'
"$PY" -B "$L563" s559 "$W559" "$WORK/walk_s559_s563.py" > "$WORK/l559.txt" 2>&1 || { cat "$WORK/l559.txt"; die "the S559 walk's lines (S563's form) were not each found exactly once"; }
"$PY" -B "$L566" s559 "$WORK/walk_s559_s563.py" "$WORK/walk_s559_s566.py" > "$WORK/l559b.txt" 2>&1 || { cat "$WORK/l559b.txt"; die "the S559 walk's lines S566 changes were not each found exactly once"; }
( cd "$WORK" && "$PY" -B "$W559" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w6" --shared "$SHARED" --dump "$WORK/b559.json" > "$WORK/s559base.txt" 2>&1 ) || { tail -3 "$WORK/s559base.txt"; die "the S559 walk's baseline could not be taken on the live files"; }
( cd "$WORK" && "$PY" -B "$WORK/walk_s559_s566.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w7" --shared "$SHARED" --baseline "$WORK/b559.json" --from-widget "$W559FROM" > "$WORK/s559.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s559.txt" | cut -c1-400; die "the S559 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s559.txt" | tail -1 | sed 's/^/    S559 walk (J1 \/ J3 in S563'"'"'s form, O3 \/ O4 in S566'"'"'s) on the new files: /'
( cd "$WORK" && "$PY" -B "$W557" "$WORK/noam" "$WORK/snap.db" --work "$WORK/w8" --shared "$SHARED" --dump "$WORK/b557.json" > "$WORK/s557base.txt" 2>&1 ) || { tail -3 "$WORK/s557base.txt"; die "the S557 walk's baseline could not be taken"; }
( cd "$WORK" && "$PY" -B "$W557" "$WORK/built" "$WORK/snap.db" --work "$WORK/w9" --shared "$SHARED" --baseline "$WORK/b557.json" > "$WORK/s557.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s557.txt" | cut -c1-400; die "the S557 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s557.txt" | tail -1 | sed 's/^/    S557 walk on the new files: /'
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$W555" "$WORK/built" "$WORK/snap.db" --work "$WORK/w10" --shared "$SHARED" > "$WORK/s555.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s555.txt" | cut -c1-400; die "the S555 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s555.txt" | tail -1 | sed 's/^/    S555 walk on the new files: /'
"$PY" -B "$L559" "$W551" "$WORK/walk_s551_s559.py" > "$WORK/s551lines.txt" 2>&1 || { cat "$WORK/s551lines.txt"; die "the S551 walk's three agreed lines (S559's) were not each found exactly once"; }
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$WORK/walk_s551_s559.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w11" --shared "$SHARED" > "$WORK/s551.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s551.txt" | cut -c1-400; die "the S551 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s551.txt" | tail -1 | sed 's/^/    S551 walk (S559'"'"'s three agreed lines) on the new files: /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run)"; exit 0; fi

log "backups beside the live files, and the database by the backup API (BEFORE the data step)"
for f in $FILES; do
  P="$(pin PIN_FROM_$(base "$f").txt)"; cp -p "$APP/$f" "$APP/$f.bak_S571_${P:0:8}" || die "backup of $f failed"
done
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S571_$STAMP" || die "database backup failed"
echo "    the two files .bak_S571_<from8> . $(basename "$DB").bak_S571_$STAMP ($NEWF was absent: nothing to back up)"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING every file from its backup ($NEWF removed: it was absent)"
  for f in $FILES; do
    P="$(pin PIN_FROM_$(base "$f").txt)"
    cp -p "$APP/$f.bak_S571_${P:0:8}" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"
  done
  rm -f "$APP/$NEWF"
  eval "$RESTART" || true
  for f in $FILES; do
    [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || { echo "RESTORE FAILED ($f) -- run the UNDO line in the README"; exit 2; }
  done
  [ -e "$APP/$NEWF" ] && { echo "RESTORE FAILED ($NEWF still there) -- run the UNDO line in the README"; exit 2; }
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE SCAN APP DOES NOT ANSWER (${RH:-nothing}) -- tell Claude now"; exit 2; }
  echo "    files back at $(for f in $FILES; do printf '%s ' "$(md5 "$APP/$f" | cut -c1-8)"; done)(the FROM pins), $NEWF absent; healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays -- the data step only ADDED three tables, two indexes, the seeded places and one setting, read by nothing the old files run)"
  exit 1
}

log "the data step: batteries.py's own ensure() from the built file -- three tables, two indexes, the 15 seeded places, batteries.since (additive, idempotent)"
( cd "$WORK/built" && "$PY" -B "$WORK/built/$NEWF" --ensure "$DB" ) > "$WORK/ensure.txt" 2>&1 || { cat "$WORK/ensure.txt"; die "the data step (ensure) failed -- the database backup is $(basename "$DB").bak_S571_$STAMP"; }
( cd "$WORK/built" && "$PY" -B "$WORK/built/$NEWF" --ensure "$DB" ) > "$WORK/ensure2.txt" 2>&1 || { cat "$WORK/ensure2.txt"; die "the data step's second run failed -- the database backup is $(basename "$DB").bak_S571_$STAMP"; }
sed 's/^/    /' "$WORK/ensure.txt"; sed 's/^/    a second run: /' "$WORK/ensure2.txt"
"$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); t={r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}; n=c.execute('SELECT COUNT(*) FROM battery_place WHERE seed_key IS NOT NULL').fetchone()[0]; s=c.execute(\"SELECT COUNT(*) FROM settings WHERE key='batteries.since'\").fetchone()[0]; sys.exit(0 if {'battery_place','battery_fit','battery_upkeep'} <= t and n == 15 and s == 1 else 1)" "$DB" || die "the data step did not leave the three tables, the 15 seeded places and batteries.since"
echo "    battery_place (15 seeded places), battery_fit, battery_upkeep and batteries.since present (no existing row changed)"

log "place (batteries.py new and sorting_desk.py first, the app's own file last), and read the md5 back"
for f in $NEWF sorting_desk.py asset_register.py; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || restore; done
[ "$(md5 "$APP/$NEWF")" = "$(pin PIN_TO_batteries.txt)" ] || restore
echo "    placed: the three scan-app files at the kit's pins (finance untouched)"

log "restart $SERVICE (only), then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S571_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
for pg in desk batteries; do
  X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/$pg")"; [ "$X" = "302" ] && break; sleep 2; done
  if [ "$X" = "302" ]; then echo "    /$pg answers 302 (the login gate -- expected, not a failure): mounted and gated"
  else echo "    /$pg answered ${X:-nothing}, not 302: it did not mount, or its login gate is open"; restore; fi
done

echo
echo "$KIT: DONE."
echo "  PINS (read back): $(for f in $FILES $NEWF; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)"
echo "  WHAT HIS PAGES NOW SHOW: the scan app's menu has 'Batteries' after Machines. The page: four totals (due for replacement,"
echo "  warranty ends within 30 days, B.L. bill awaited, battery places); four groups -- Online UPS, Small UPS, Generator and inverters,"
echo "  Vehicles -- with the 15 places (names only; nothing recorded yet: 'Not recorded yet' until each battery is entered once);"
echo "  'New battery fitted' on every row (B.L.: warranty 12, the bill or 'bill awaited'; Jasoria: price, old battery, net, warranty from"
echo "  the card, bill and card); a place's history; '+ Add a battery place'. On the sorting desk a B.L. Computers or Jasoria paper offers"
echo "  'Battery fitted at <place> on <date> — this bill?' (one tap links it; the paper is never changed). Renewals has a 'Batteries'"
echo "  card. A new UPS, inverter or vehicle added in Machines gets its place by itself. Shavez sees nothing until he switches"
echo "  'Batteries for Shavez' ON on his Switches card (then the clinic and lab places only); reception never."
echo "  UNDO (one line): $(for f in $FILES; do P="$(pin PIN_FROM_$(base "$f").txt)"; printf '\\cp -p %s %s && ' "$APP/$f.bak_S571_${P:0:8}" "$APP/$f"; done)mv -f $APP/$NEWF $APP/$NEWF.off_S571 && systemctl restart $SERVICE"
exit 0
