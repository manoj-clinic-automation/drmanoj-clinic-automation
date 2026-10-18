#!/bin/bash
# install_s582.sh -- S582_XRAY_COSTS (D736; board _numbers v480 -> v481; the owner, 13:03 IST 18-Oct-2026: "it needs to be also under the
# xray expenses section, so that I can assess expenses of the xray department also"). One owner-only page, X-ray expenses (/xray, the menu
# item "X-ray costs" right after Batteries): month by month, X-ray films (The month's own rule), the papers he marks for X-ray, the
# service / repair / cover of the machines he ticks, the batteries of the places he ticks -- each rupee once. A paper keeps its one group.
# Files: /root/assetapp/batteries.py (S575's TO 40eb8a91 -> the kit's TO; two counted edits: the guarded mount at the end of init, the menu
# item after Batteries) and the NEW /root/assetapp/xray_costs.py. Read only, pinned: asset_register.py, sorting_desk.py, clinic_papers.py,
# stationery.py, asset_machine.py, scanner_widget.js, claude_reader.py, claude_reread.py and the parent's /root/finance/packs.py. Never
# touched: every finance and Sanjeevni file.
# assets.db: ADDITIVE -- one new table xray_mark (+ its unique index), made by the mount; the DATA STEP (after health) seeds the owner's own
# words: the paper B-0163, the battery places "Digital X-ray" and "X-ray detector (FDR) battery" (each absent one skipped with one line).
# BUILD_NORM_v1 s3 order (S575's shape, S582_BRIEF_R1 B3): gates -> the build lock -> FROM pins (and the read-only pins) -> rebuild from the
# live bytes -> TO pins -> compile (both pythons) -> S582's walk + control on a scratch copy of the live database (made-up rows), then
# S575's, S571's (its line 354 in S582's form, on a copy at its install-day shape), S568's (on a copy with the stationery list at its install-day shape -- s568_copy_s582.py), S566's, S563's (with its tidy fetch), S560's
# (+ pack), S548's, S559's, S557's, S555's and S551's walks (DRY=1 stops here) -> backups (batteries.py; the database by the backup API,
# BEFORE the restart that makes the table) -> place xray_costs.py, then batteries.py -> md5 read-back -> restart assetapp ONLY -> /healthz
# 200, then /desk, /batteries and /xray 302 (302 ONLY) -> the data step -> what his pages now show -> undo line. A failure after placing
# puts batteries.py back byte-identically, takes xray_costs.py out (kept beside as .undone_S582), restarts assetapp; the database backup stays.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S582_XRAY_COSTS/install_s582.sh
set -u
KIT="S582_XRAY_COSTS"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KITS="${S582_KITS_DIR:-$(cd "$HERE/.." && pwd)}"
APP="${S582_APP_DIR:-/root/assetapp}"
FIN="${S582_FIN_DIR:-/root/finance}"
SERVICE="${S582_SERVICE:-assetapp}"
HEALTH="${S582_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S582_PYTHON:-python3}"
PYV="${S582_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S582_RESTART_CMD:-systemctl restart $SERVICE}"
SHARED="${S582_SHARED_DIR:-/root/shared}"
LOCK="${S582_LOCK:-/root/deploy/.claude_code_build.lock}"
TRIES="${S582_HEALTH_TRIES:-20}"
W559FROM="${S582_W559_FROM:-$APP/scanner_widget.js.bak_S559_1143c77b}"     # the widget before S559 (S559's walk J1 compares against it)
PK_BEFORE="${S582_PACK_BEFORE:-$FIN/packs.py.bak_S560_d86d351a}"            # packs.py before S560 (S560's pack walk P8 compares against it)
PK_B568="${S582_PACK_BEFORE_S568:-$FIN/packs.py.bak_S568_048d2ad8}"         # packs.py before S568 (S568's walk I8 compares against it)
F="batteries.py"                                                             # edited
N="xray_costs.py"                                                            # new
READONLY="sorting_desk.py asset_register.py clinic_papers.py stationery.py asset_machine.py scanner_widget.js claude_reader.py claude_reread.py"   # read only; pinned
PF="packs.py"                                                                # the parent's, read only; pinned, never placed
S563BAK="sorting_desk.py:a4623438 clinic_papers.py:88963eac asset_register.py:9daed9ea asset_machine.py:0caec41e scanner_widget.js:1128ac97"   # S563's own backups (its tidy fetch)
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
if [ -z "${S582_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S582_DB:-${DB0:-$APP/assets.db}}"
STAMP="$(date +%Y%m%d_%H%M%S)"
K575="$KITS/S575_BATTERY_SETUP"
K571="$KITS/S571_BATTERIES"
K568="$KITS/S568_STATIONERY_STOCK"
K566="$KITS/S566_SCANAPP_LAST_FIXES"
K563="$KITS/S563_SCANAPP_TIDY"
W575="$K575/walk_s575.py"; C575="$K575/s571_copy_s575.py"
W571="$K571/walk_s571.py"
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
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; rm -rf /tmp/s582dev /tmp/s582kit /tmp/s582reh; rm -f "$APP/$F.tmp" "$APP/$N.tmp"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }   # S323 K1 C1: the build's box scratch too
trap cleanup EXIT

log "gates (the box, root, the files)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
for k in PIN_FROM_batteries.txt PIN_TO_batteries.txt PIN_TO_xray_costs.txt; do v="$(pin $k)"; [ ${#v} -eq 32 ] || die "$k is missing in the kit"; done
for f in $READONLY $PF; do v="$(pin PIN_READ_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base "$f").txt is missing in the kit"; done
for p in PIN_READ_widget_before_s559.txt PIN_READ_packs_before_s560.txt PIN_READ_packs_before_s568.txt PIN_ITEM3_s563_clinic_papers.txt PIN_TIDY566_clinic_papers.txt PIN_TIDY568_clinic_papers.txt; do v="$(pin $p)"; [ ${#v} -eq 32 ] || die "$p is missing in the kit"; done
for f in make_s582.py walk_s582.py lines_s582.py s568_copy_s582.py $N; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
for w in "$W575" "$C575" "$W571" "$W568" "$M568" "$L568" "$W566" "$M566" "$L566" "$W563" "$M563" "$L563" "$K563/fetch_s563.py" "$W560" "$W560P" "$W559" "$L559" "$W557" "$W555" "$W551" "$W548"; do [ -f "$w" ] || die "the earlier walk $w (regression) is not beside this kit"; done
[ -f "$APP/$F" ] || die "$APP/$F is missing -- S571 / S575 are not installed; S582 changes S575's batteries.py"
for f in $READONLY; do [ -f "$APP/$f" ] || die "$APP/$f missing"; done
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
L="$(md5 "$APP/$F")"
if [ "$L" = "$(pin PIN_TO_batteries.txt)" ]; then
  if [ -f "$APP/$N" ] && [ "$(md5 "$APP/$N")" = "$(pin PIN_TO_xray_costs.txt)" ]; then
    echo "$KIT: ALREADY INSTALLED (batteries.py and xray_costs.py at the kit's pins)"
    echo "  PINS (read back): $F $L . $N $(md5 "$APP/$N")"
    exit 0
  fi
  die "$F is at the kit's TO pin but $N is $([ -f "$APP/$N" ] && echo "at $(md5 "$APP/$N" | cut -c1-8), not the kit's" || echo "missing") -- a half install; run the UNDO line in the README, then this line again"
fi
P="$(pin PIN_FROM_batteries.txt)"
[ "$L" = "$P" ] || die "$F is ${L:0:8}, not the pinned ${P:0:8} (S575's TO) -- another kit moved it; rebuild S582 on the new bytes"
echo "    $F ${P:0:8} ok (S575's TO)"
[ -e "$APP/$N" ] && die "$APP/$N is already there ($(md5 "$APP/$N" | cut -c1-8)) and batteries.py is not at the kit's TO -- not this kit's file; stop and report"
echo "    $N not there yet (new)"
for f in $READONLY; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f (read only) is ${L:0:8}, not the pinned ${P:0:8} -- the walk was proven on other bytes"
  echo "    $f ${P:0:8} ok (read only, not touched)"
done
L="$(md5 "$FIN/$PF")"; P="$(pin PIN_READ_packs.txt)"
[ "$L" = "$P" ] || die "$PF (the parent's, read only) is ${L:0:8}, not the pinned ${P:0:8} -- the earlier walks were proven on other bytes"
echo "    $PF ${P:0:8} ok (the parent's, read only, not touched)"
for f in scan_register.py purchase_app.py; do
  P="$(pin PIN_READ_$(base "$f").txt)"; L="$(md5 "$FIN/$f")"
  [ "$L" = "$P" ] && echo "    $f ${P:0:8} (Sanjeevni's, read only)" || echo "    $f is ${L:0:8}, not ${P:0:8} (Sanjeevni's, read only; S568's walk runs its query as it is now)"
done

WORK="$(mktemp -d /tmp/s582_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built" "$WORK/am" "$WORK/noam" "$WORK/s563from" "$WORK/s563cp3" "$WORK/tidy566" "$WORK/tidy" "$WORK/fin568" "$WORK/w571s"
for f in $F $READONLY; do cp "$APP/$f" "$WORK/live_in/"; done
"$PY" -B "$HERE/make_s582.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
sed 's/^/    /' "$WORK/make.txt"
for f in $READONLY; do cp "$APP/$f" "$WORK/built/"; done
B="$(md5 "$WORK/built/$F")"; P="$(pin PIN_TO_batteries.txt)"
[ "$B" = "$P" ] || die "the rebuilt $F is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $F ${B:0:8} = the kit's pin"
B="$(md5 "$WORK/built/$N")"; P="$(pin PIN_TO_xray_costs.txt)"
[ "$B" = "$P" ] || die "the built $N is ${B:0:8}, the kit says ${P:0:8}"; echo "    $N ${B:0:8} = the kit's pin"
for p in $S563BAK; do f=${p%%:*}; h=${p##*:}; cp "$APP/$f.bak_S563_$h" "$WORK/s563from/$f"; done
"$PY" -B "$M563" "$WORK/s563from" "$WORK/s563cp3" --cp-item3-only > "$WORK/make563.txt" 2>&1 || { cat "$WORK/make563.txt"; die "S563's builder refused (item 3 only, from S563's own backups)"; }
[ "$(md5 "$WORK/s563cp3/clinic_papers.py")" = "$(pin PIN_ITEM3_s563_clinic_papers.txt)" ] || die "S563's item-3-only clinic_papers.py is not at its pin"
"$PY" -B "$M566" --cp-on "$WORK/s563cp3/clinic_papers.py" "$WORK/tidy566/clinic_papers.py" > "$WORK/maketidy566.txt" 2>&1 || { cat "$WORK/maketidy566.txt"; die "S566's clinic_papers edits did not apply to S563's item-3-only file"; }
[ "$(md5 "$WORK/tidy566/clinic_papers.py")" = "$(pin PIN_TIDY566_clinic_papers.txt)" ] || die "S566's tidy comparison file is not at its pin"
"$PY" -B "$M568" --cp-on "$WORK/tidy566/clinic_papers.py" "$WORK/tidy/clinic_papers.py" > "$WORK/maketidy.txt" 2>&1 || { cat "$WORK/maketidy.txt"; die "S568's clinic_papers edits did not apply to S566's tidy comparison file"; }
B="$(md5 "$WORK/tidy/clinic_papers.py")"; P="$(pin PIN_TIDY568_clinic_papers.txt)"
[ "$B" = "$P" ] || die "S568 on S566's tidy comparison file is ${B:0:8}, the kit says ${P:0:8}"
echo "    S563's tidy comparison rebuilt: S563 item 3 only -> S566's edits -> S568's edits = ${B:0:8} (S582 leaves clinic_papers.py as it is)"
cp "$WORK/built/asset_machine.py" "$WORK/am/"
for f in sorting_desk.py clinic_papers.py asset_register.py scanner_widget.js claude_reader.py claude_reread.py stationery.py batteries.py xray_costs.py; do cp "$WORK/built/$f" "$WORK/noam/"; done
for f in scan_register.py purchase_app.py porders.py order_sheet.py; do cp "$FIN/$f" "$WORK/fin568/"; done
cp "$PK_B568" "$WORK/fin568/$PF"

log "compile on both pythons"
mkdir -p "$WORK/cc"; cp "$WORK/built/$F" "$WORK/built/$N" "$WORK/cc/"
( cd "$WORK/cc" && "$PY" -m py_compile $F $N ) || die "the built files do not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $F $N ) || die "the built files do not compile on $PYV"; echo "    $F and $N compile on $PY and $PYV"; else echo "    compile on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "walks on a scratch copy of the database (made-up rows; nothing sent anywhere) -- S582's walk and control; S575's; S571's (its line 354 in S582's form, on a copy at its install-day shape), S568's (its stationery list at its install-day shape), S566's, S563's (and its tidy fetch), the S560 (+ pack), S548, S559, S557, S555 and S551 walks"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$WORK/snap.db" || die "the scratch copy of the database failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s582.py" "$WORK/built" "$WORK/snap.db" --from "$WORK/live_in" --work "$WORK/w1" --shared "$SHARED" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/walk.txt" | cut -c1-400; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk: /'
grep -E 'counts' "$WORK/walk.txt" | cut -c1-400 | sed 's/^/      /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s582.py" "$WORK/live_in" "$WORK/snap.db" --from "$WORK/live_in" --work "$WORK/w2" --shared "$SHARED" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL' "$WORK/control.txt"; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (the live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | sed 's/^/    /'
( cd "$WORK" && "$PY" -B "$W575" "$WORK/built" "$WORK/snap.db" --work "$WORK/w13" --shared "$SHARED" > "$WORK/s575.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s575.txt" | cut -c1-400; die "the S575 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s575.txt" | tail -1 | sed 's/^/    S575 walk on the new files: /'
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$WORK/snap.db" "$WORK/snap571.db" || die "the S571 walk's copy failed"
"$PY" -B "$C575" "$WORK/snap571.db" > "$WORK/s571copy.txt" 2>&1 || { cat "$WORK/s571copy.txt"; die "the S571 walk's copy could not be put at S571's install-day shape"; }
sed 's/^/    /' "$WORK/s571copy.txt"
"$PY" -B "$HERE/lines_s582.py" s571 "$W571" "$WORK/w571s/walk_s571_s582.py" > "$WORK/l571.txt" 2>&1 || { cat "$WORK/l571.txt"; die "the S571 walk's line 354 (S582's form) was not found exactly once"; }
( cd "$WORK" && "$PY" -B "$WORK/w571s/walk_s571_s582.py" "$WORK/built" "$WORK/snap571.db" --work "$WORK/w0" --shared "$SHARED" > "$WORK/s571.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s571.txt" | cut -c1-400; die "the S571 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s571.txt" | tail -1 | sed 's/^/    S571 walk (its I1 menu line in S582'"'"'s form; its copy at its install-day shape) on the new files: /'
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$WORK/snap.db" "$WORK/snap568.db" || die "the S568 walk's copy failed"
"$PY" -B "$HERE/s568_copy_s582.py" "$WORK/snap568.db" > "$WORK/s568copy.txt" 2>&1 || { cat "$WORK/s568copy.txt"; die "the S568 walk's copy could not be put at S568's install-day shape"; }
sed 's/^/    /' "$WORK/s568copy.txt"
cp "$FIN/$PF" "$WORK/built/$PF"
( cd "$WORK" && "$PY" -B "$W568" "$WORK/built" "$WORK/snap568.db" --work "$WORK/w12" --shared "$SHARED" --fin "$WORK/fin568" > "$WORK/s568.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s568.txt" | cut -c1-400; die "the S568 walk is RED on the built files"; }
rm -f "$WORK/built/$PF"
grep -E 'checks' "$WORK/s568.txt" | tail -1 | sed 's/^/    S568 walk on the new files (its copy with the stationery list at its install-day shape -- empty; its I8 "before" = packs.py before S568, as when it was proven): /'
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
grep -E 'pack checks' "$WORK/pack.txt" | tail -1 | sed 's/^/    S560 pack walk (P2 \/ P8 in S568'"'"'s form) on packs.py as it is (S582 does not touch it): /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$W548" "$FIN/$PF" "$FIN" > "$WORK/s548.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s548.txt"; die "the S548 pack walk is RED"; }
grep -E 'checks' "$WORK/s548.txt" | tail -1 | sed 's/^/    S548 pack walk: /'
"$PY" -B "$L563" s559 "$W559" "$WORK/walk_s559_s563.py" > "$WORK/l559.txt" 2>&1 || { cat "$WORK/l559.txt"; die "the S559 walk's lines (S563's form) were not each found exactly once"; }
"$PY" -B "$L566" s559 "$WORK/walk_s559_s563.py" "$WORK/walk_s559_s566.py" > "$WORK/l559b.txt" 2>&1 || { cat "$WORK/l559b.txt"; die "the S559 walk's lines S566 changes were not each found exactly once"; }
( cd "$WORK" && "$PY" -B "$W559" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w6" --shared "$SHARED" --dump "$WORK/b559.json" > "$WORK/s559base.txt" 2>&1 ) || { tail -3 "$WORK/s559base.txt"; die "the S559 walk's baseline could not be taken on the live files"; }
( cd "$WORK" && "$PY" -B "$WORK/walk_s559_s566.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w7" --shared "$SHARED" --baseline "$WORK/b559.json" --from-widget "$W559FROM" > "$WORK/s559.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s559.txt" | cut -c1-400; die "the S559 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s559.txt" | tail -1 | sed 's/^/    S559 walk (J1 \/ J3 in S563'"'"'s form, O3 \/ O4 in S566'"'"'s; M1 unchanged) on the new files: /'
( cd "$WORK" && "$PY" -B "$W557" "$WORK/noam" "$WORK/snap.db" --work "$WORK/w8" --shared "$SHARED" --dump "$WORK/b557.json" > "$WORK/s557base.txt" 2>&1 ) || { tail -3 "$WORK/s557base.txt"; die "the S557 walk's baseline could not be taken"; }
( cd "$WORK" && "$PY" -B "$W557" "$WORK/built" "$WORK/snap.db" --work "$WORK/w9" --shared "$SHARED" --baseline "$WORK/b557.json" > "$WORK/s557.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s557.txt" | cut -c1-400; die "the S557 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s557.txt" | tail -1 | sed 's/^/    S557 walk on the new files: /'
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$W555" "$WORK/built" "$WORK/snap.db" --work "$WORK/w10" --shared "$SHARED" > "$WORK/s555.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s555.txt" | cut -c1-400; die "the S555 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s555.txt" | tail -1 | sed 's/^/    S555 walk on the new files: /'
"$PY" -B "$L559" "$W551" "$WORK/walk_s551_s559.py" > "$WORK/s551lines.txt" 2>&1 || { cat "$WORK/s551lines.txt"; die "the S551 walk's three agreed lines (S559's) were not each found exactly once"; }
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$WORK/walk_s551_s559.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w11" --shared "$SHARED" > "$WORK/s551.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s551.txt" | cut -c1-400; die "the S551 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s551.txt" | tail -1 | sed 's/^/    S551 walk (S559'"'"'s three agreed lines) on the new files: /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run)"; exit 0; fi

log "backups beside the live file, and the database by the backup API (BEFORE the restart that makes the new table)"
P="$(pin PIN_FROM_batteries.txt)"
cp -p "$APP/$F" "$APP/$F.bak_S582_${P:0:8}" || die "backup of $F failed"
"$PY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DB" "$DB.bak_S582_$STAMP" || die "database backup failed"
echo "    $F.bak_S582_${P:0:8} . $(basename "$DB").bak_S582_$STAMP ($N is new: nothing to back up)"

hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
restore(){
  echo "RESTORING $F from its backup and taking $N out"
  P="$(pin PIN_FROM_batteries.txt)"
  cp -p "$APP/$F.bak_S582_${P:0:8}" "$APP/$F.tmp" && mv -f "$APP/$F.tmp" "$APP/$F"
  [ -f "$APP/$N" ] && mv -f "$APP/$N" "$APP/$N.undone_S582"
  eval "$RESTART" || true
  [ "$(md5 "$APP/$F")" = "$P" ] && [ ! -e "$APP/$N" ] || { echo "RESTORE FAILED ($F / $N) -- run the UNDO line in the README"; exit 2; }
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE SCAN APP DOES NOT ANSWER (${RH:-nothing}) -- tell Claude now"; exit 2; }
  echo "    $F back at $(md5 "$APP/$F" | cut -c1-8) (the FROM pin); $N out (kept as $N.undone_S582); healthz 200 after the restore"
  echo "$KIT: NOT INSTALLED (restored; the empty table xray_mark may stay in the database -- additive, read by nothing else; the database backup stays)"
  exit 1
}

log "place ($N first -- nothing imports it until batteries.py does), and read the md5s back"
if ! { cp "$WORK/built/$N" "$APP/$N.tmp" && mv -f "$APP/$N.tmp" "$APP/$N"; }; then restore; fi
if ! { cp "$WORK/built/$F" "$APP/$F.tmp" && mv -f "$APP/$F.tmp" "$APP/$F"; }; then restore; fi
[ "$(md5 "$APP/$N")" = "$(pin PIN_TO_xray_costs.txt)" ] || restore
[ "$(md5 "$APP/$F")" = "$(pin PIN_TO_batteries.txt)" ] || restore
for f in $READONLY; do [ "$(md5 "$APP/$f")" = "$(pin PIN_READ_$(base "$f").txt)" ] || restore; done
echo "    placed: $F and $N at the kit's pins; the read-only files unchanged (finance untouched)"

log "restart $SERVICE (only), then health"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S582_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
for pg in desk batteries xray; do
  X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/$pg")"; [ "$X" = "302" ] && break; sleep 2; done
  if [ "$X" = "302" ]; then echo "    /$pg answers 302 (the login gate -- expected, not a failure): mounted and gated"
  else echo "    /$pg answered ${X:-nothing}, not 302: it did not mount, or its login gate is open"; restore; fi
done

log "the data step: the table (idempotent) and the owner's own words (the paper B-0163, the two X-ray battery places)"
"$PY" -B "$APP/$N" --ensure "$DB" > "$WORK/data.txt" 2>&1 || { cat "$WORK/data.txt"; echo "    the data step failed"; restore; }
sed 's/^/    /' "$WORK/data.txt"

echo
echo "$KIT: DONE."
echo "  PINS (read back): $F $(md5 "$APP/$F") . $N $(md5 "$APP/$N")"
echo "  WHAT HIS PAGES NOW SHOW: a new item 'X-ray costs' in his menu, right after Batteries (his only -- Shavez and reception see nothing new)."
echo "  It opens 'X-ray expenses — <this month>' with previous / next months and one line: the total this month and since the first month."
echo "  Four folds, each with its month total and rows: X-ray films (as The month counts them), Papers marked for X-ray (a paper adds"
echo "  only when The month counts it -- an awaiting challan shows 'not counted: challan awaiting'), Machines marked for X-ray (service,"
echo "  repair, cover -- none ticked by the system; 'FDR'-named machines are listed first), Batteries of the X-ray places. The data step's"
echo "  lines above say which of B-0163 and the two X-ray battery places were marked. '+ Mark a paper for X-ray' takes a stamp; a paper"
echo "  keeps its one group. Each rupee once: a spend, cover or battery's own paper is shown under it, not counted again."
P="$(pin PIN_FROM_batteries.txt)"
echo "  UNDO (one line): \\cp -p $APP/$F.bak_S582_${P:0:8} $APP/$F && mv -f $APP/$N $APP/$N.undone_S582 && systemctl restart $SERVICE"
exit 0
