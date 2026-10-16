#!/bin/bash
# install_s568.sh -- S568_STATIONERY_STOCK (D646 PLANNED line, board v451; the owner's rulings D730): Stationery & packaging.
# A new clinic consumables group "Stationery & packaging" (the desk, The month, the papers page; no existing paper moved); the
# stationery item list with rates (stationery.py, the owner's "Stationery" page); received from the desk -- a challan's, an
# estimate slip's and a lone bill's matched lines, counted when read, so the stock goes up once; issued on "Stationery diya" (Roman
# Hinglish; the owner at once, a manager only with the switch stationery.issue_on ON -- installed OFF; reception never); counts
# (the first is the opening stock, a later one records "not accounted for"); the mixed-challan tick; "Add a paper from a file" on
# the desk with ONE preset -- the Aumni envelopes, a Sanjeevni pharmacy expense paid by Dr MK's card (kind 'Pharmacy expense',
# never 'Pharmacy'); and THE PARENT'S packs.py, build_bundle's kind filter only: the accountants' bundles take bills and invoices only.
# Files: /root/assetapp/sorting_desk.py, clinic_papers.py, asset_register.py, the NEW stationery.py (absent = its FROM state; present
# with other bytes = STOP); /root/finance/packs.py (not at its FROM pin = that file STOPPED and said, the rest installed).
# Read only, pinned: asset_machine.py, scanner_widget.js, claude_reader.py, claude_reread.py. Never touched: every Sanjeevni file.
# Data step (the app's own ensure path, additive, idempotent, before placing): stationery_item, stationery_line, stationery_move,
# stationery_count (+ one index) and bills.mixed -- no existing row changed.
# BUILD_NORM_v1 s3 order (S566's shape, S560's packs.py handling): gates -> the build lock -> FROM pins (and the read-only pins) ->
# rebuild from the live bytes -> TO pins -> compile (both pythons) -> S568's walk + control, S566's walk, S563's walk with its tidy
# fetch, the S560 (+ pack, P2 / P8 in S568's form), S548, S559, S557, S555 and S551 walks on a scratch copy (DRY=1 stops here) ->
# backups (files; the database by the backup API) -> the data step -> place -> md5 read-back -> restart assetapp -> /healthz 200,
# /desk 302 and /stationery 302 (302 ONLY) -> restart clinic-finance (only when packs.py was placed) -> /finance/healthz 200 and no
# "packs NOT mounted" in its journal -> what his pages now show -> undo line. A failure after placing restores every file
# byte-identically (stationery.py removed: it was absent) and restarts both services.
# Run as root on the VPS: bash /root/deploy/repo/deploy_kits/S568_STATIONERY_STOCK/install_s568.sh
set -u
KIT="S568_STATIONERY_STOCK"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KITS="${S568_KITS_DIR:-$(cd "$HERE/.." && pwd)}"
APP="${S568_APP_DIR:-/root/assetapp}"
FIN="${S568_FIN_DIR:-/root/finance}"
SERVICE="${S568_SERVICE:-assetapp}"
FSERVICE="${S568_FIN_SERVICE:-clinic-finance}"
HEALTH="${S568_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
FHEALTH="${S568_FIN_HEALTH_URL:-http://127.0.0.1:8106/finance/healthz}"
PY="${S568_PYTHON:-python3}"
PYV="${S568_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S568_RESTART_CMD:-systemctl restart $SERVICE}"
FRESTART="${S568_FIN_RESTART_CMD:-systemctl restart $FSERVICE}"
SHARED="${S568_SHARED_DIR:-/root/shared}"
LOCK="${S568_LOCK:-/root/deploy/.claude_code_build.lock}"
JOURNAL="${S568_JOURNAL_CMD:-journalctl}"
TRIES="${S568_HEALTH_TRIES:-20}"
W559FROM="${S568_W559_FROM:-$APP/scanner_widget.js.bak_S559_1143c77b}"     # the widget before S559 (S559's walk J1 compares against it)
PK_BEFORE="${S568_PACK_BEFORE:-$FIN/packs.py.bak_S560_d86d351a}"            # packs.py before S560 (S560's pack walk P8 compares against it)
FILES="sorting_desk.py clinic_papers.py asset_register.py"                   # placed in this order, the app's own file last
NEWF="stationery.py"                                                         # new: absent before; placed before asset_register.py
READONLY="asset_machine.py scanner_widget.js claude_reader.py claude_reread.py"   # read only; pinned (the walks import them)
PF="packs.py"
S563BAK="sorting_desk.py:a4623438 clinic_papers.py:88963eac asset_register.py:9daed9ea asset_machine.py:0caec41e scanner_widget.js:1128ac97"   # S563's own backups (its tidy fetch)
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
if [ -z "${S568_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S568_DB:-${DB0:-$APP/assets.db}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
K566="$KITS/S566_SCANAPP_LAST_FIXES"
K563="$KITS/S563_SCANAPP_TIDY"
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
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES $NEWF; do rm -f "$APP/$f.tmp"; done; rm -f "$FIN/$PF.tmp"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap cleanup EXIT

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for f in $FILES $PF; do for k in FROM TO; do v="$(pin PIN_${k}_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_${k}_$(base "$f").txt is missing in the kit"; done; done
v="$(pin PIN_TO_stationery.txt)"; [ ${#v} -eq 32 ] || die "PIN_TO_stationery.txt is missing in the kit"
for f in $READONLY; do v="$(pin PIN_READ_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base "$f").txt is missing in the kit"; done
for p in PIN_READ_widget_before_s559.txt PIN_READ_packs_before_s560.txt PIN_ITEM3_s563_clinic_papers.txt PIN_TIDY566_clinic_papers.txt PIN_TIDY_clinic_papers.txt; do v="$(pin $p)"; [ ${#v} -eq 32 ] || die "$p is missing in the kit"; done
for f in make_s568.py walk_s568.py lines_s568.py stationery.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
[ "$(md5 "$HERE/stationery.py")" = "$(pin PIN_TO_stationery.txt)" ] || die "the kit's stationery.py is not at its pin"
for w in "$W566" "$M566" "$L566" "$W563" "$M563" "$L563" "$K563/fetch_s563.py" "$W560" "$W560P" "$W559" "$L559" "$W557" "$W555" "$W551" "$W548"; do [ -f "$w" ] || die "the earlier walk $w (regression) is not beside this kit"; done
for f in $FILES $READONLY; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
for p in $S563BAK; do f=${p%%:*}; h=${p##*:}; [ -f "$APP/$f.bak_S563_$h" ] && [ "$(md5 "$APP/$f.bak_S563_$h" | cut -c1-8)" = "$h" ] || die "S563's backup $f.bak_S563_$h (its tidy fetch is re-run from it) is not in $APP"; done
[ -f "$FIN/$PF" ] || die "$FIN/$PF missing"
[ -f "$W559FROM" ] && [ "$(md5 "$W559FROM")" = "$(pin PIN_READ_widget_before_s559.txt)" ] || die "the widget before S559 (S559's walk compares against it) is not at $W559FROM"
[ -f "$PK_BEFORE" ] && [ "$(md5 "$PK_BEFORE")" = "$(pin PIN_READ_packs_before_s560.txt)" ] || die "packs.py before S560 (S560's pack walk compares against it) is not at $PK_BEFORE"
for f in scan_register.py purchase_app.py porders.py order_sheet.py; do [ -f "$FIN/$f" ] || die "the Sanjeevni reader $FIN/$f (read only: the walk runs its query) is missing"; done
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
{ [ -f "$APP/$NEWF" ] && [ "$(md5 "$APP/$NEWF")" = "$(pin PIN_TO_stationery.txt)" ]; } || ALL_TO=0
PKL="$(md5 "$FIN/$PF")"
if [ "$ALL_TO" = 1 ] && { [ "$PKL" = "$(pin PIN_TO_packs.txt)" ] || [ "$PKL" != "$(pin PIN_FROM_packs.txt)" ]; }; then
  echo "$KIT: ALREADY INSTALLED (the scan app's four files at the kit's pins; packs.py $( [ "$PKL" = "$(pin PIN_TO_packs.txt)" ] && echo "at its TO pin" || echo "${PKL:0:8} -- neither pin: left as it is"))"
  echo "  PINS (read back): $(for f in $FILES $NEWF; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)$PF $PKL"
  exit 0
fi
for f in $FILES; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- another kit moved it; rebuild S568 on the new bytes"
  echo "    $f ${P:0:8} ok"
done
[ -e "$APP/$NEWF" ] && die "$NEWF is already in $APP ($(md5 "$APP/$NEWF" | cut -c1-8)) and the other files are not at the kit's pins -- it is not this kit's; stopped"
echo "    $NEWF absent (its FROM state) ok"
for f in $READONLY; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f (read only) is ${L:0:8}, not the pinned ${P:0:8} -- the walk was proven on other bytes"
  echo "    $f ${P:0:8} ok (read only, not touched)"
done
PKDO=1
if [ "$PKL" = "$(pin PIN_FROM_packs.txt)" ]; then echo "    $PF ${PKL:0:8} ok (the parent's: build_bundle's kind filter only)"
else PKDO=0; echo "    $PF is ${PKL:0:8}, not the pinned $(pin PIN_FROM_packs.txt | cut -c1-8) -- THAT FILE IS STOPPED (left as it is, not placed); the rest goes on (the brief)"; fi
for f in scan_register.py purchase_app.py; do
  P="$(pin PIN_READ_$(base "$f").txt)"; L="$(md5 "$FIN/$f")"
  [ "$L" = "$P" ] && echo "    $f ${P:0:8} (Sanjeevni's, read only: reads pharmacy scans by kind='Pharmacy')" || echo "    $f is ${L:0:8}, not ${P:0:8} (Sanjeevni's, read only; the walk runs its query as it is now)"
done

WORK="$(mktemp -d /tmp/s568_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built" "$WORK/am" "$WORK/noam" "$WORK/s563from" "$WORK/s563cp3" "$WORK/tidy566" "$WORK/tidy" "$WORK/pkb"
for f in $FILES $READONLY; do cp "$APP/$f" "$WORK/live_in/"; done
[ "$PKDO" = 1 ] && cp "$FIN/$PF" "$WORK/live_in/"
"$PY" -B "$HERE/make_s568.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
sed 's/^/    /' "$WORK/make.txt"
for f in $READONLY; do cp "$APP/$f" "$WORK/built/"; done
for f in $FILES; do
  B="$(md5 "$WORK/built/$f")"; P="$(pin PIN_TO_$(base "$f").txt)"
  [ "$B" = "$P" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's pin"
done
[ "$(md5 "$WORK/built/$NEWF")" = "$(pin PIN_TO_stationery.txt)" ] || die "stationery.py in the build is not at its pin"; echo "    $NEWF $(pin PIN_TO_stationery.txt | cut -c1-8) = the kit's pin (new)"
if [ "$PKDO" = 1 ]; then
  B="$(md5 "$WORK/built/$PF")"; P="$(pin PIN_TO_packs.txt)"; [ "$B" = "$P" ] || die "the rebuilt $PF is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $PF ${B:0:8} = the kit's pin"
  cp "$WORK/built/$PF" "$WORK/pkb/$PF"
else
  cp "$FIN/$PF" "$WORK/pkb/$PF"
fi
for p in $S563BAK; do f=${p%%:*}; h=${p##*:}; cp "$APP/$f.bak_S563_$h" "$WORK/s563from/$f"; done
"$PY" -B "$M563" "$WORK/s563from" "$WORK/s563cp3" --cp-item3-only > "$WORK/make563.txt" 2>&1 || { cat "$WORK/make563.txt"; die "S563's builder refused (item 3 only, from S563's own backups)"; }
[ "$(md5 "$WORK/s563cp3/clinic_papers.py")" = "$(pin PIN_ITEM3_s563_clinic_papers.txt)" ] || die "S563's item-3-only clinic_papers.py is not at its pin"
"$PY" -B "$M566" --cp-on "$WORK/s563cp3/clinic_papers.py" "$WORK/tidy566/clinic_papers.py" > "$WORK/maketidy566.txt" 2>&1 || { cat "$WORK/maketidy566.txt"; die "S566's clinic_papers edits did not apply to S563's item-3-only file"; }
[ "$(md5 "$WORK/tidy566/clinic_papers.py")" = "$(pin PIN_TIDY566_clinic_papers.txt)" ] || die "S566's tidy comparison file is not at its pin"
"$PY" -B "$HERE/make_s568.py" --cp-on "$WORK/tidy566/clinic_papers.py" "$WORK/tidy/clinic_papers.py" > "$WORK/maketidy.txt" 2>&1 || { cat "$WORK/maketidy.txt"; die "S568's clinic_papers edits did not apply to S566's tidy comparison file"; }
B="$(md5 "$WORK/tidy/clinic_papers.py")"; P="$(pin PIN_TIDY_clinic_papers.txt)"
[ "$B" = "$P" ] || die "S568 on S566's tidy comparison file is ${B:0:8}, the kit says ${P:0:8}"
echo "    S563's tidy comparison rebuilt: S563 item 3 only -> S566's edits -> S568's edits = ${B:0:8} (the kit's pin)"
cp "$WORK/built/asset_machine.py" "$WORK/am/"
for f in sorting_desk.py clinic_papers.py asset_register.py scanner_widget.js claude_reader.py claude_reread.py; do cp "$WORK/built/$f" "$WORK/noam/"; done

log "compile on both pythons"
mkdir -p "$WORK/cc"; for f in $FILES $NEWF; do cp "$WORK/built/$f" "$WORK/cc/"; done; cp "$WORK/pkb/$PF" "$WORK/cc/"
( cd "$WORK/cc" && "$PY" -m py_compile $FILES $NEWF $PF ) || die "a built file does not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $FILES $NEWF $PF ) || die "a built file does not compile on $PYV"; echo "    compiles on $PY and $PYV"; else echo "    compiles on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walks on a scratch copy of the database (made-up rows; nothing sent anywhere) -- S568's walk and control; S566's walk; S563's walk and its tidy fetch; the S560 (+ pack), S548, S559, S557, S555 and S551 walks"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$WORK/snap.db" || die "the scratch copy of the database failed"
cp "$WORK/pkb/$PF" "$WORK/built/$PF"
NOPK=""; [ "$PKDO" = 1 ] || NOPK="--no-pack"
( cd "$WORK" && "$PY" -B "$HERE/walk_s568.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w1" --shared "$SHARED" --fin "$FIN" $NOPK > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt" | cut -c1-400; die "the walk is RED on the built files"; }
rm -f "$WORK/built/$PF"
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E 'counts' "$WORK/walk.txt" | sed 's/^/      /'
cp "$FIN/$PF" "$WORK/live_in/$PF"
( cd "$WORK" && "$PY" -B "$HERE/walk_s568.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w2" --shared "$SHARED" --fin "$FIN" $NOPK --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | tail -1 | sed 's/^/    /'
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
if [ "$PKDO" = 1 ]; then
  "$PY" -B "$HERE/lines_s568.py" s560pack "$W560P" "$WORK/walk_s560_pack_s568.py" > "$WORK/l560p.txt" 2>&1 || { cat "$WORK/l560p.txt"; die "the S560 pack walk's lines S568 changes (P2, P8) were not each found exactly once"; }
  ( cd "$WORK" && HOME="$WORK" "$PY" -B "$WORK/walk_s560_pack_s568.py" "$WORK/pkb/$PF" "$FIN" --before "$PK_BEFORE" > "$WORK/pack.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/pack.txt"; die "the S560 pack walk is RED on the built packs.py"; }
  grep -E 'pack checks' "$WORK/pack.txt" | tail -1 | sed 's/^/    S560 pack walk (P2 \/ P8 in S568'"'"'s form) on the new packs.py: /'
else
  ( cd "$WORK" && HOME="$WORK" "$PY" -B "$W560P" "$FIN/$PF" "$FIN" --before "$PK_BEFORE" > "$WORK/pack.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/pack.txt"; die "the S560 pack walk is RED"; }
  grep -E 'pack checks' "$WORK/pack.txt" | tail -1 | sed 's/^/    S560 pack walk (packs.py not placed, as it is): /'
fi
( cd "$WORK" && HOME="$WORK" "$PY" -B "$W548" "$WORK/pkb/$PF" "$FIN" > "$WORK/s548.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s548.txt"; die "the S548 pack walk is RED"; }
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
  P="$(pin PIN_FROM_$(base "$f").txt)"; cp -p "$APP/$f" "$APP/$f.bak_S568_${P:0:8}" || die "backup of $f failed"
done
if [ "$PKDO" = 1 ]; then P="$(pin PIN_FROM_packs.txt)"; cp -p "$FIN/$PF" "$FIN/$PF.bak_S568_${P:0:8}" || die "backup of $PF failed"; fi
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S568_$STAMP" || die "database backup failed"
echo "    the three files .bak_S568_<from8>$( [ "$PKDO" = 1 ] && echo " . packs.py.bak_S568_$(pin PIN_FROM_packs.txt | cut -c1-8)") . $(basename "$DB").bak_S568_$STAMP ($NEWF was absent: nothing to back up)"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING every file from its backup ($NEWF removed: it was absent)"
  for f in $FILES; do
    P="$(pin PIN_FROM_$(base "$f").txt)"
    cp -p "$APP/$f.bak_S568_${P:0:8}" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"
  done
  rm -f "$APP/$NEWF"
  if [ "$PKDO" = 1 ]; then P="$(pin PIN_FROM_packs.txt)"; cp -p "$FIN/$PF.bak_S568_${P:0:8}" "$FIN/$PF.tmp" && mv -f "$FIN/$PF.tmp" "$FIN/$PF"; fi
  eval "$RESTART" || true
  [ "$PKDO" = 1 ] && { eval "$FRESTART" || true; }
  for f in $FILES; do
    [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || { echo "RESTORE FAILED ($f) -- run the UNDO line in the README"; exit 2; }
  done
  [ -e "$APP/$NEWF" ] && { echo "RESTORE FAILED ($NEWF still there) -- run the UNDO line in the README"; exit 2; }
  if [ "$PKDO" = 1 ]; then [ "$(md5 "$FIN/$PF")" = "$(pin PIN_FROM_packs.txt)" ] || { echo "RESTORE FAILED ($PF) -- run the UNDO line in the README"; exit 2; }; fi
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  RF=""; for i in $(seq 1 "$TRIES"); do RF="$(hc "$FHEALTH")"; [ "$RF" = "200" ] && break; sleep 2; done
  [ "$RH" = "200" ] && [ "$RF" = "200" ] || { echo "RESTORED THE FILES, BUT A SERVICE DOES NOT ANSWER (scan app ${RH:-nothing}, finance ${RF:-nothing}) -- tell Claude now"; exit 2; }
  echo "    files back at $(for f in $FILES; do printf '%s ' "$(md5 "$APP/$f" | cut -c1-8)"; done)$(md5 "$FIN/$PF" | cut -c1-8) (the FROM pins), $NEWF absent; healthz 200 and /finance/healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays -- the data step only ADDED four empty tables, one index and one column, read by nothing the old files run)"
  exit 1
}

log "the data step: the app's own ensure() from the built files -- stationery.py's four tables, sorting_desk's bills.mixed (additive, idempotent)"
( cd "$WORK/built" && "$PY" -B -c "import sqlite3,sys,importlib.util as u
for n, f in (('sd568', 'sorting_desk.py'), ('st568', 'stationery.py')):
    s = u.spec_from_file_location(n, f); m = u.module_from_spec(s); s.loader.exec_module(m)
    c = sqlite3.connect(sys.argv[1], timeout=30); m.ensure(c); c.close()" "$DB" ) > "$WORK/ensure.txt" 2>&1 || { cat "$WORK/ensure.txt"; die "the data step (ensure) failed -- the database backup is $(basename "$DB").bak_S568_$STAMP"; }
"$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); t={r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}; k={r[1] for r in c.execute('PRAGMA table_info(bills)')}; sys.exit(0 if {'stationery_item','stationery_line','stationery_move','stationery_count'} <= t and 'mixed' in k else 1)" "$DB" || die "the data step did not leave the four tables and the column"
echo "    stationery_item, stationery_line, stationery_move, stationery_count and bills.mixed present (no existing row changed)"

log "place (the modules first -- stationery.py new -- the app's own file last; then the parent's packs.py), and read the md5 back"
for f in sorting_desk.py clinic_papers.py $NEWF asset_register.py; do
  if ! { cp "$WORK/built/$f" "$APP/$f.tmp" && mv -f "$APP/$f.tmp" "$APP/$f"; }; then restore; fi
done
if [ "$PKDO" = 1 ]; then if ! { cp "$WORK/pkb/$PF" "$FIN/$PF.tmp" && mv -f "$FIN/$PF.tmp" "$FIN/$PF"; }; then restore; fi; fi
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || restore; done
[ "$(md5 "$APP/$NEWF")" = "$(pin PIN_TO_stationery.txt)" ] || restore
if [ "$PKDO" = 1 ]; then [ "$(md5 "$FIN/$PF")" = "$(pin PIN_TO_packs.txt)" ] || restore; fi
echo "    placed: the four scan-app files$( [ "$PKDO" = 1 ] && echo " and packs.py") at the kit's pins"

log "restart $SERVICE$( [ "$PKDO" = 1 ] && echo ", then $FSERVICE"), then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S568_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
for pg in desk stationery; do
  X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/$pg")"; [ "$X" = "302" ] && break; sleep 2; done
  if [ "$X" = "302" ]; then echo "    /$pg answers 302 (the login gate -- expected, not a failure): mounted and gated"
  else echo "    /$pg answered ${X:-nothing}, not 302: it did not mount, or its login gate is open"; restore; fi
done
if [ "$PKDO" = 1 ]; then
  FT0="$(date -d '-1 second' '+%Y-%m-%d %H:%M:%S')"
  eval "$FRESTART" || restore
  FC=""; for i in $(seq 1 "$TRIES"); do sleep 2; FC="$(hc "$FHEALTH")"; [ "$FC" = "200" ] && break; done
  [ "$FC" = "200" ] || { echo "    /finance/healthz answered ${FC:-nothing}"; restore; }
  sleep 1
  if "$JOURNAL" -u "$FSERVICE" --since "$FT0" --no-pager -q 2>/dev/null | grep -q "packs NOT mounted"; then
    echo "    /finance/healthz 200, but packs.py did not load (the finance journal says 'packs NOT mounted')"; restore
  fi
  echo "    /finance/healthz 200; packs.py loaded (no 'packs NOT mounted' in the finance journal since the restart)"
else
  echo "    $FSERVICE not restarted (packs.py was not placed)"
fi

echo
echo "$KIT: DONE.$( [ "$PKDO" = 1 ] || echo " (packs.py STOPPED: it was not at its FROM pin -- the pack fix is NOT in; say so to the chat)")"
echo "  PINS (read back): $(for f in $FILES $NEWF; do printf '%s %s . ' "$f" "$(md5 "$APP/$f")"; done)$PF $(md5 "$FIN/$PF")"
echo "  WHAT HIS PAGES NOW SHOW: the sorting desk has a fifth clinic consumables button, 'Stationery & packaging'; with it chosen, the"
echo "  paper's lines can be matched to the stationery list, '+ Add to the list' or 'not a stock item' (a rate that differs from the"
echo "  list is flagged); a challan or bill there or on NK Pathology can be ticked 'mixed: clinic + lab items'. The month has the"
echo "  Stationery & packaging section, and 'Sanjeevni — pharmacy expenses' under Kept apart. The menu has 'Stationery' (his only):"
echo "  the stock -- in stock, received, issued by place, last rate, low stock, Count, the item list. 'Stationery diya' is the staff"
echo "  screen; it stays OFF for managers until he switches 'Stationery diya for managers' ON on his Switches card. The desk's list has"
echo "  '+ Add a paper from a file' (the Aumni preset: a Sanjeevni pharmacy expense, paid by Dr MK's card). The accountants' bundles"
echo "  take bills and invoices only (an estimate slip or a paid-on-challan paper no longer goes in)."
echo "  UNDO (one line): $(for f in $FILES; do P="$(pin PIN_FROM_$(base "$f").txt)"; printf '\\cp -p %s %s && ' "$APP/$f.bak_S568_${P:0:8}" "$APP/$f"; done)mv -f $APP/$NEWF $APP/$NEWF.off_S568 && $( [ "$PKDO" = 1 ] && { P="$(pin PIN_FROM_packs.txt)"; printf '\\cp -p %s %s && ' "$FIN/$PF.bak_S568_${P:0:8}" "$FIN/$PF"; })systemctl restart $SERVICE$( [ "$PKDO" = 1 ] && echo " && systemctl restart $FSERVICE")"
exit 0
