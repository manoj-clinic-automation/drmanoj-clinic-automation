#!/bin/bash
# install_s601.sh -- S601_PHARMACY_BILLS_READ_BY_CLAUDE (D747; board _numbers v529 -> v530; the owner, 15:41 IST 19-Oct-2026: "Start Claude
# to read the pharmacy bills. Keep Sarvam switched off in settings so that the code is made once.")
# Claude fills the pharmacy bills (header and items) as it fills the clinic's papers; the pharmacy "beside" read is retired; Sarvam is
# switched OFF by a setting (read.sarvam), its code kept; a paper Claude cannot read is tried again by the app three times over two hours.
# Files: /root/assetapp/asset_register.py (c39c084e -> the kit's TO) and /root/assetapp/claude_reread.py (d9b75e78 -> the kit's TO), both
# rebuilt here from the live bytes (make_s601.py, anchored edits, each anchor exactly once) -- the ONLY two files changed. Read only, pinned,
# STOP if moved: claude_reader.py, sorting_desk.py, clinic_papers.py, batteries.py (S582's TO), stationery.py (S585's TO), xray_costs.py,
# asset_machine.py, scanner_widget.js, /root/shared/sarvam_ocr.py, the parent's /root/finance/packs.py. The Sanjeevni files purchase_app.py,
# scan_register.py, item_check.py, amir_day.py, porders.py, order_sheet.py: their md5s printed, placed never, proven unmoved after placing.
# assets.db: no DDL, no new table. ONE data step after health: settings read.sarvam = off (the owner's word), rehearsed on the scratch copy
# first; new audit rows (filled, read_retry) are additive. Service assetapp (gunicorn -w 2, port 8030), restarted ONCE.
# ORDER (S585's shape + the Sanjeevni gates): gates (the box, root, the window 08:00-23:49 IST, SUMS, KIT_ID, the pins present) -> the build
# lock -> FROM pins and the read-only md5s (STOP on a moved one) -> the service environment (ASSETS_DB, ASSETS_UPLOADS,
# SCANAPP_ANTHROPIC_KEY_FILE; the module's defaults when absent) -> the key file present and claude_reader.state = on (STOP otherwise) ->
# the crontab read (a claude_reread line: expected none) -> rebuild from the live bytes -> TO pins -> compile (both pythons) -> the walk on
# the OLD files (every control red; its dump) then on the NEW files (green, against the dump) -> the data step rehearsed on the scratch copy
# -> S585's chain of earlier walks (S585, S582, S575, S571, S568, S566, S563 with its tidy fetch, S560 + pack, S548, S559, S557, S555, S551)
# -> DRY stops -> the state BEFORE (the live files on a copy; the NEW files on the same copy) -> backups (the two files; the database by the
# backup API, BEFORE the restart) -> the two files staged and renamed in ONE command -> md5 read-back -> ONE restart of assetapp -> /healthz
# 200, /admin 302, /bills 302 (302 ONLY) -> journal clean -> the data step -> the state AFTER (Claude ON, Sarvam OFF on the owner's card) ->
# nothing else moved -> md5 read-back. Red after placing: both files back byte-identically in one command, one restart, healthz; the setting
# is NOT written on a red; the database backup stays. The build lock stays held until the report is written (CLAUDE.md). set -u, never -e.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S601_PHARMACY_BILLS_READ_BY_CLAUDE/install_s601.sh
# (DRY=1 in front: every gate, the build, every walk; nothing placed, no lock.)
set -u
KIT="S601_PHARMACY_BILLS_READ_BY_CLAUDE"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KITS="${S601_KITS_DIR:-$(cd "$HERE/.." && pwd)}"
APP="${S601_APP_DIR:-/root/assetapp}"
FIN="${S601_FIN_DIR:-/root/finance}"
SHARED="${S601_SHARED_DIR:-/root/shared}"
SERVICE="${S601_SERVICE:-assetapp}"
HEALTH="${S601_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S601_PYTHON:-/usr/bin/python3}"
PYV="${S601_PYTHON_VENV:-/root/wa/venv/bin/python3}"
RESTART="${S601_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S601_LOCK:-/root/deploy/.claude_code_build.lock}"
TRIES="${S601_HEALTH_TRIES:-20}"
JOURNALCTL="${S601_JOURNALCTL:-journalctl}"
W559FROM="${S601_W559_FROM:-$APP/scanner_widget.js.bak_S559_1143c77b}"     # the widget before S559 (S559's walk J1 compares against it)
PK_BEFORE="${S601_PACK_BEFORE:-$FIN/packs.py.bak_S560_d86d351a}"            # packs.py before S560 (S560's pack walk P8 compares against it)
PK_B568="${S601_PACK_BEFORE_S568:-$FIN/packs.py.bak_S568_048d2ad8}"         # packs.py before S568 (S568's walk I8 compares against it)
BT_B582="${S601_BATTERIES_BEFORE_S582:-$APP/batteries.py.bak_S582_40eb8a91}" # batteries.py before S582 (S582's walk X11 compares against it)
EDITED="asset_register.py claude_reread.py"                                 # the two files placed
READONLY="claude_reader.py sorting_desk.py clinic_papers.py batteries.py stationery.py xray_costs.py asset_machine.py scanner_widget.js"   # pinned, never touched
SHRO="sarvam_ocr.py"                                                        # /root/shared, read only, pinned
PF="packs.py"                                                               # the parent's, read only; pinned, never placed
SANJ="purchase_app.py scan_register.py item_check.py amir_day.py porders.py order_sheet.py"   # Sanjeevni's: printed, never opened for writing
S563BAK="sorting_desk.py:a4623438 clinic_papers.py:88963eac asset_register.py:9daed9ea asset_machine.py:0caec41e scanner_widget.js:1128ac97"   # S563's own backups (its tidy fetch)
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ local b="${1%.py}"; echo "${b%.js}"; }
hc(){ curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; }
copydb(){ "$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True, timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
mask(){ sed -E 's/[0-9]{10,}/##########/g'; }
SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
UP0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_UPLOADS=//p' | head -1)"
KF0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^SCANAPP_ANTHROPIC_KEY_FILE=//p' | head -1)"
unset SVC_ENV
DB="${S601_DB:-${DB0:-$APP/assets.db}}"                                     # the module's default when the unit carries none (asset_register.py:27)
UPLOADS="${S601_UPLOADS:-${UP0:-$APP/uploads}}"                             # asset_register.py:28
KEYF="${S601_KEY_FILE:-${KF0:-/root/.scanapp_secrets/anthropic.key}}"      # claude_reader.py:21
STAMP="$(date +%Y%m%d_%H%M%S)"
K585="$KITS/S585_STATIONERY_ISSUE_MANY"
K582="$KITS/S582_XRAY_COSTS"
K575="$KITS/S575_BATTERY_SETUP"
K571="$KITS/S571_BATTERIES"
K568="$KITS/S568_STATIONERY_STOCK"
K566="$KITS/S566_SCANAPP_LAST_FIXES"
K563="$KITS/S563_SCANAPP_TIDY"
W585="$K585/walk_s585.py"; C582="$K585/s582_copy_s585.py"
W582="$K582/walk_s582.py"; L582="$K582/lines_s582.py"; C568="$K582/s568_copy_s582.py"
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
HAVE_LOCK=0; PLACED=0; DONE=0
WORK=""
cleanup(){ [ -n "$WORK" ] && [ -z "${S601_KEEP_SCRATCH:-}" ] && rm -rf "$WORK"; rm -f "$APP/asset_register.py.tmp_s601" "$APP/claude_reread.py.tmp_s601"
           find "$HERE" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
           if [ "$HAVE_LOCK" = 1 ] && [ "$DONE" = 0 ]; then rm -rf "$LOCK"; echo "    (the build lock released: nothing was installed)"; fi; }
trap cleanup EXIT
export PYTHONDONTWRITEBYTECODE=1

log "gates (the box, root, the window, SUMS, KIT_ID, the pins, the earlier kits)"
case "$(hostname)" in *srv1746119*) ;; *) die "this is not srv1746119";; esac
[ "$(id -u)" = "0" ] || die "run as root"
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"
{ [ "$HH" -ge 8 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } || die "$(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:00-23:49 IST"
( cd "$HERE" && md5sum -c SUMS.md5 >/dev/null 2>&1 ) || die "SUMS.md5 gate failed -- the kit is not the published bytes"
[ "$(awk 'NR==1{print $3}' "$HERE/KIT_ID.txt")" = "$KIT" ] || die "KIT_ID.txt names another kit"
for f in $EDITED; do for k in FROM TO; do v="$(pin PIN_${k}_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_${k}_$(base "$f").txt is missing in the kit"; done; done
for f in $READONLY $SHRO $PF $SANJ; do v="$(pin PIN_READ_$(base "$f").txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base "$f").txt is missing in the kit"; done
for p in PIN_READ_widget_before_s559.txt PIN_READ_packs_before_s560.txt PIN_READ_packs_before_s568.txt PIN_READ_batteries_before_s582.txt PIN_ITEM3_s563_clinic_papers.txt PIN_TIDY566_clinic_papers.txt PIN_TIDY568_clinic_papers.txt; do v="$(pin $p)"; [ ${#v} -eq 32 ] || die "$p is missing in the kit"; done
for f in make_s601.py walk_s601.py; do [ -f "$HERE/$f" ] || die "kit file $f missing"; done
for w in "$W585" "$C582" "$W582" "$L582" "$C568" "$W575" "$C575" "$W571" "$W568" "$M568" "$L568" "$W566" "$M566" "$L566" "$W563" "$M563" "$L563" "$K563/fetch_s563.py" "$W560" "$W560P" "$W559" "$L559" "$W557" "$W555" "$W551" "$W548"; do [ -f "$w" ] || die "the earlier walk $w (regression) is not beside this kit"; done
for f in $EDITED $READONLY; do [ -f "$APP/$f" ] || die "$APP/$f is missing"; done
[ -f "$SHARED/$SHRO" ] || die "$SHARED/$SHRO is missing"
[ -f "$FIN/$PF" ] || die "$FIN/$PF missing"
for f in $SANJ; do [ -f "$FIN/$f" ] || die "the Sanjeevni file $FIN/$f (read only) is missing"; done
for p in $S563BAK; do f=${p%%:*}; h=${p##*:}; [ -f "$APP/$f.bak_S563_$h" ] && [ "$(md5 "$APP/$f.bak_S563_$h" | cut -c1-8)" = "$h" ] || die "S563's backup $f.bak_S563_$h (its tidy fetch is re-run from it) is not in $APP"; done
[ -f "$W559FROM" ] && [ "$(md5 "$W559FROM")" = "$(pin PIN_READ_widget_before_s559.txt)" ] || die "the widget before S559 (S559's walk compares against it) is not at $W559FROM"
[ -f "$PK_BEFORE" ] && [ "$(md5 "$PK_BEFORE")" = "$(pin PIN_READ_packs_before_s560.txt)" ] || die "packs.py before S560 (S560's pack walk compares against it) is not at $PK_BEFORE"
[ -f "$PK_B568" ] && [ "$(md5 "$PK_B568")" = "$(pin PIN_READ_packs_before_s568.txt)" ] || die "packs.py before S568 (S568's walk I8 compares against it) is not at $PK_B568"
[ -f "$BT_B582" ] && [ "$(md5 "$BT_B582")" = "$(pin PIN_READ_batteries_before_s582.txt)" ] || die "batteries.py before S582 (S582's walk X11 compares against it) is not at $BT_B582"
[ -f "$DB" ] || die "no database at the service's path"
[ -d "$UPLOADS" ] || die "no uploads folder at the service's path"
[ -x "$PY" ] || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
command -v curl >/dev/null || die "no curl"
echo "    $APP, $SHARED and $FIN ok; the window $(TZ=Asia/Kolkata date '+%H:%M IST'); SUMS and KIT_ID ok; the earlier kits beside this one"
echo "    the service environment: ASSETS_DB $([ -n "$DB0" ] && echo 'from the unit' || echo 'absent -> the module default'), ASSETS_UPLOADS $([ -n "$UP0" ] && echo 'from the unit' || echo 'absent -> the module default'), SCANAPP_ANTHROPIC_KEY_FILE $([ -n "$KF0" ] && echo 'from the unit' || echo 'absent -> the module default') (paths not shown)"

log "pins -- the live bytes must be the ones this kit was built on (ALREADY INSTALLED read first)"
ALL_TO=1; for f in $EDITED; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then
  SW="$("$PY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); r=c.execute(\"SELECT value FROM settings WHERE key='read.sarvam'\").fetchone(); print(r[0] if r else 'absent')" "$DB" 2>/dev/null || echo unread)"
  echo "$KIT: ALREADY INSTALLED (both files at the kit's pins; the setting read.sarvam = $SW)"
  for f in $EDITED; do echo "  PINS (read back): $f $(md5 "$APP/$f")"; done
  exit 0
fi
for f in $EDITED; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_FROM_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} -- someone changed it since the brief: STOP, rebuild S601 on the new bytes"
  echo "    $f ${P:0:8} ok (FROM)"
done
for f in $READONLY; do
  L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base "$f").txt)"
  [ "$L" = "$P" ] || die "$f (read only) is ${L:0:8}, not the pinned ${P:0:8} -- the walk was proven on other bytes: STOP"
  echo "    $f ${P:0:8} ok (read only, not touched)"
done
L="$(md5 "$SHARED/$SHRO")"; P="$(pin PIN_READ_sarvam_ocr.txt)"
[ "$L" = "$P" ] || die "$SHRO (/root/shared, read only) is ${L:0:8}, not the pinned ${P:0:8}: STOP"
echo "    $SHRO ${P:0:8} ok (/root/shared, read only, not touched)"
L="$(md5 "$FIN/$PF")"; P="$(pin PIN_READ_packs.txt)"
[ "$L" = "$P" ] || die "$PF (the parent's, read only) is ${L:0:8}, not the pinned ${P:0:8} -- the earlier walks were proven on other bytes: STOP"
echo "    $PF ${P:0:8} ok (the parent's, read only, not touched)"
declare -A SANJ0
for f in $SANJ; do
  P="$(pin PIN_READ_$(base "$f").txt)"; L="$(md5 "$FIN/$f")"; SANJ0[$f]="$L"
  [ "$L" = "$P" ] && echo "    $f ${P:0:8} (Sanjeevni's, read only, never placed)" || echo "    $f is ${L:0:8}, not ${P:0:8} as the brief read it (Sanjeevni's, read only, never placed; the S568 walk runs its query as it is now)"
done
CRON0="$(crontab -l 2>/dev/null | md5sum | cut -c1-32)"
CRONR="$(crontab -l 2>/dev/null | grep -c claude_reread || true)"
echo "    the crontab: $(crontab -l 2>/dev/null | wc -l | awk '{print $1}') lines; claude_reread lines ${CRONR:-0} (expected 0: the re-read is one-shot, no cron, by design)"

log "the Claude reader on the box: the key file present and claude_reader.state = on (else STOP: Sarvam is not switched off while nothing else can read)"
[ -s "$KEYF" ] || die "the Claude key file is absent or empty at the service's path -- nothing else can read: STOP"
ST="$(cd "$APP" && SCANAPP_ANTHROPIC_KEY_FILE="$KEYF" "$PY" -B -c 'import sqlite3,sys; sys.path.insert(0,"."); import claude_reader as c; con=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); print(c.state(con)); print("model=" + str(c.setting(con, "read.claude_model", ""))); print("calls_today=%s cap=%s" % (c.calls_today(con), c.cap(con)))' "$DB" 2>&1)" || die "claude_reader.state could not be read: $ST"
echo "$ST" | sed 's/^/    claude_reader: /'
[ "$(echo "$ST" | head -1)" = "on" ] || die "claude_reader.state is '$(echo "$ST" | head -1)', not 'on': STOP"
echo "    the key file present ($(stat -c %s "$KEYF") bytes, never shown); read.claude = on"

if [ -z "${DRY:-}" ]; then
  log "the server-wide build lock (one build at a time on the shared server)"
  mkdir -p "$(dirname "$LOCK")"
  if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
    die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- run it again when it is free"; fi
  echo "    the build lock is ours ($(date '+%Y-%m-%d %H:%M:%S %Z')); it stays held until the report is written"
else
  log "DRY=1: no lock, nothing placed -- every gate, the build and every walk run"
fi

WORK="$(mktemp -d /tmp/s601_install_XXXX)" && [ -n "$WORK" ] && [ -d "$WORK" ] || die "no temporary folder"

log "rebuild on the box, from the live bytes (each anchor exactly once)"
mkdir -p "$WORK/live_in" "$WORK/built" "$WORK/am" "$WORK/noam" "$WORK/s563from" "$WORK/s563cp3" "$WORK/tidy566" "$WORK/tidy" "$WORK/fin568" "$WORK/w571s" "$WORK/s582from"
for f in $EDITED $READONLY; do cp "$APP/$f" "$WORK/live_in/"; done
"$PY" -B "$HERE/make_s601.py" "$WORK/live_in" "$WORK/built" > "$WORK/make.txt" 2>&1 || { cat "$WORK/make.txt"; die "the builder refused"; }
sed 's/^/    /' "$WORK/make.txt"
for f in $READONLY; do cp "$APP/$f" "$WORK/built/"; done
for f in $EDITED; do
  B="$(md5 "$WORK/built/$f")"; P="$(pin PIN_TO_$(base "$f").txt)"
  [ "$B" = "$P" ] || die "the rebuilt $f is ${B:0:8}, the kit says ${P:0:8}"; echo "    rebuilt $f ${B:0:8} = the kit's TO pin"
done
for p in $S563BAK; do f=${p%%:*}; h=${p##*:}; cp "$APP/$f.bak_S563_$h" "$WORK/s563from/$f"; done
"$PY" -B "$M563" "$WORK/s563from" "$WORK/s563cp3" --cp-item3-only > "$WORK/make563.txt" 2>&1 || { cat "$WORK/make563.txt"; die "S563's builder refused (item 3 only, from S563's own backups)"; }
[ "$(md5 "$WORK/s563cp3/clinic_papers.py")" = "$(pin PIN_ITEM3_s563_clinic_papers.txt)" ] || die "S563's item-3-only clinic_papers.py is not at its pin"
"$PY" -B "$M566" --cp-on "$WORK/s563cp3/clinic_papers.py" "$WORK/tidy566/clinic_papers.py" > "$WORK/maketidy566.txt" 2>&1 || { cat "$WORK/maketidy566.txt"; die "S566's clinic_papers edits did not apply to S563's item-3-only file"; }
[ "$(md5 "$WORK/tidy566/clinic_papers.py")" = "$(pin PIN_TIDY566_clinic_papers.txt)" ] || die "S566's tidy comparison file is not at its pin"
"$PY" -B "$M568" --cp-on "$WORK/tidy566/clinic_papers.py" "$WORK/tidy/clinic_papers.py" > "$WORK/maketidy.txt" 2>&1 || { cat "$WORK/maketidy.txt"; die "S568's clinic_papers edits did not apply to S566's tidy comparison file"; }
B="$(md5 "$WORK/tidy/clinic_papers.py")"; P="$(pin PIN_TIDY568_clinic_papers.txt)"
[ "$B" = "$P" ] || die "S568 on S566's tidy comparison file is ${B:0:8}, the kit says ${P:0:8}"
echo "    S563's tidy comparison rebuilt: S563 item 3 only -> S566's edits -> S568's edits = ${B:0:8} (S601 leaves clinic_papers.py as it is)"
cp "$WORK/built/asset_machine.py" "$WORK/am/"
for f in sorting_desk.py clinic_papers.py asset_register.py scanner_widget.js claude_reader.py claude_reread.py stationery.py batteries.py xray_costs.py; do cp "$WORK/built/$f" "$WORK/noam/"; done
for f in sorting_desk.py clinic_papers.py asset_register.py scanner_widget.js claude_reader.py claude_reread.py stationery.py asset_machine.py; do cp "$WORK/built/$f" "$WORK/s582from/"; done
cp "$BT_B582" "$WORK/s582from/batteries.py"                                  # S582's FROM: batteries.py before S582, no xray_costs.py
for f in scan_register.py purchase_app.py porders.py order_sheet.py; do cp "$FIN/$f" "$WORK/fin568/"; done
cp "$PK_B568" "$WORK/fin568/$PF"

log "compile on both pythons"
mkdir -p "$WORK/cc"; for f in $EDITED; do cp "$WORK/built/$f" "$WORK/cc/"; done; cp "$HERE/make_s601.py" "$HERE/walk_s601.py" "$WORK/cc/"
( cd "$WORK/cc" && "$PY" -m py_compile $EDITED make_s601.py walk_s601.py ) || die "the built files do not compile on $PY"
if [ -x "$PYV" ]; then ( cd "$WORK/cc" && "$PYV" -m py_compile $EDITED make_s601.py walk_s601.py ) || die "the built files do not compile on $PYV"; echo "    $EDITED, make_s601.py and walk_s601.py compile on $PY and $PYV"; else echo "    compile on $PY ($PYV not present)"; fi
rm -rf "$WORK/cc"

log "the walk on a scratch copy of the database (made-up rows; never the key; nothing sent anywhere): the OLD files first (every control red, its dump), then the NEW files (green, against the dump)"
copydb "$DB" "$WORK/snap.db" || die "the scratch copy of the database failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s601.py" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w0" --shared "$SHARED" --dump "$WORK/dump_old.json" --expect-red > "$WORK/control.txt" 2>&1 ) || { grep -E 'checks|^CONTROL|^RED|Traceback|Error' "$WORK/control.txt" | mask | cut -c1-400; die "the NEGATIVE CONTROL did not go red on the live files"; }
grep -E 'checks' "$WORK/control.txt" | tail -1 | sed 's/^/    control (the live files, must be red): /'
grep -E '^CONTROL' "$WORK/control.txt" | sed 's/^/    /'
( cd "$WORK" && "$PY" -B "$HERE/walk_s601.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w1" --shared "$SHARED" --old-dump "$WORK/dump_old.json" > "$WORK/walk.txt" 2>&1 ) || { grep -E '^RED|checks|Traceback|Error' "$WORK/walk.txt" | mask | cut -c1-600; die "the walk is RED on the built files"; }
grep -E 'checks' "$WORK/walk.txt" | tail -1 | sed 's/^/    walk (the built files): /'
grep -E '^(GREEN|RED)' "$WORK/walk.txt" | cut -c1-200 | sed 's/^/      /'
for f in $EDITED; do [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base "$f").txt)" ] || die "$APP/$f changed during the walk"; done

log "the data step rehearsed on the scratch copy (read.sarvam = off, one INSERT OR REPLACE; read back)"
copydb "$WORK/snap.db" "$WORK/snapds.db" || die "the data step's rehearsal copy failed"
RS="$("$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1], timeout=30); c.execute(\"INSERT OR REPLACE INTO settings(key,value) VALUES('read.sarvam','off')\"); c.commit(); print(c.execute(\"SELECT value FROM settings WHERE key='read.sarvam'\").fetchone()[0]); c.close()" "$WORK/snapds.db" 2>&1)" || die "the data step REFUSED on the scratch copy: $RS"
[ "$RS" = "off" ] || die "the data step's rehearsal read back '$RS', not 'off'"
echo "    rehearsal (scratch copy): read.sarvam = $RS; no other row touched (one key)"

log "S585's chain of earlier walks on the NEW files (regression; S582's, S571's and S568's copies at their install-day shapes; S563's tidy fetch)"
( cd "$WORK" && "$PY" -B "$W585" "$WORK/built" "$WORK/snap.db" --from "$WORK/live_in" --work "$WORK/w2" --shared "$SHARED" > "$WORK/s585.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s585.txt" | mask | cut -c1-400; die "the S585 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s585.txt" | tail -1 | sed 's/^/    S585 walk on the new files (its M1 FROM = the live files): /'
copydb "$WORK/snap.db" "$WORK/snap582.db" || die "the S582 walk's copy failed"
"$PY" -B "$C582" "$WORK/snap582.db" > "$WORK/s582copy.txt" 2>&1 || { cat "$WORK/s582copy.txt"; die "the S582 walk's copy could not be put at S582's install-day shape"; }
sed 's/^/    /' "$WORK/s582copy.txt"
( cd "$WORK" && "$PY" -B "$W582" "$WORK/built" "$WORK/snap582.db" --from "$WORK/s582from" --work "$WORK/w14" --shared "$SHARED" > "$WORK/s582.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s582.txt" | mask | cut -c1-400; die "the S582 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s582.txt" | tail -1 | sed 's/^/    S582 walk on the new files: /'
( cd "$WORK" && "$PY" -B "$W575" "$WORK/built" "$WORK/snap.db" --work "$WORK/w13" --shared "$SHARED" > "$WORK/s575.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s575.txt" | mask | cut -c1-400; die "the S575 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s575.txt" | tail -1 | sed 's/^/    S575 walk on the new files: /'
copydb "$WORK/snap.db" "$WORK/snap571.db" || die "the S571 walk's copy failed"
"$PY" -B "$C575" "$WORK/snap571.db" > "$WORK/s571copy.txt" 2>&1 || { cat "$WORK/s571copy.txt"; die "the S571 walk's copy could not be put at S571's install-day shape"; }
sed 's/^/    /' "$WORK/s571copy.txt"
"$PY" -B "$L582" s571 "$W571" "$WORK/w571s/walk_s571_s582.py" > "$WORK/l571.txt" 2>&1 || { cat "$WORK/l571.txt"; die "the S571 walk's line 354 (S582's form) was not found exactly once"; }
( cd "$WORK" && "$PY" -B "$WORK/w571s/walk_s571_s582.py" "$WORK/built" "$WORK/snap571.db" --work "$WORK/w3" --shared "$SHARED" > "$WORK/s571.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s571.txt" | mask | cut -c1-400; die "the S571 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s571.txt" | tail -1 | sed 's/^/    S571 walk (its I1 line in S582'"'"'s form; its copy at its install-day shape) on the new files: /'
copydb "$WORK/snap.db" "$WORK/snap568.db" || die "the S568 walk's copy failed"
"$PY" -B "$C568" "$WORK/snap568.db" > "$WORK/s568copy.txt" 2>&1 || { cat "$WORK/s568copy.txt"; die "the S568 walk's copy could not be put at S568's install-day shape"; }
sed 's/^/    /' "$WORK/s568copy.txt"
cp "$FIN/$PF" "$WORK/built/$PF"
( cd "$WORK" && "$PY" -B "$W568" "$WORK/built" "$WORK/snap568.db" --work "$WORK/w12" --shared "$SHARED" --fin "$WORK/fin568" > "$WORK/s568.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s568.txt" | mask | cut -c1-400; die "the S568 walk is RED on the built files"; }
rm -f "$WORK/built/$PF"
grep -E 'checks' "$WORK/s568.txt" | tail -1 | sed 's/^/    S568 walk on the new files (its copy at its install-day shape; its I8 before = packs.py before S568): /'
( cd "$WORK" && "$PY" -B "$W566" "$WORK/built" "$WORK/snap.db" --work "$WORK/w4" --shared "$SHARED" > "$WORK/s566.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s566.txt" | mask | cut -c1-400; die "the S566 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s566.txt" | tail -1 | sed 's/^/    S566 walk on the new files: /'
"$PY" -B "$L566" s563 "$W563" "$WORK/walk_s563_s566.py" > "$WORK/l563.txt" 2>&1 || { cat "$WORK/l563.txt"; die "the S563 walk's line S566 changes was not found exactly once"; }
cp "$K563/fetch_s563.py" "$WORK/fetch_s563.py" || die "S563's fetch_s563.py (its tidy fetch) is not beside its walk"
( cd "$WORK" && "$PY" -B "$WORK/walk_s563_s566.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w5" --shared "$SHARED" --tidy-from "$WORK/tidy" > "$WORK/s563.txt" 2>&1 ) || { grep -E '^RED|checks|TIDY' "$WORK/s563.txt" | mask | cut -c1-400; die "the S563 walk (or its tidy fetch) is RED on the built files"; }
grep -E 'checks' "$WORK/s563.txt" | tail -1 | sed 's/^/    S563 walk (its F4 line in S566'"'"'s form) on the new files: /'
grep -E '^TIDY' "$WORK/s563.txt" | sed 's/^/      /'
"$PY" -B "$L563" s560 "$W560" "$WORK/walk_s560_s563.py" > "$WORK/l560.txt" 2>&1 || { cat "$WORK/l560.txt"; die "the S560 walk's line (S563's form) was not found exactly once"; }
( cd "$WORK" && "$PY" -B "$WORK/walk_s560_s563.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w6" --shared "$SHARED" > "$WORK/s560.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s560.txt" | mask | cut -c1-400; die "the S560 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s560.txt" | tail -1 | sed 's/^/    S560 walk (its K2 line in S563'"'"'s form) on the new files: /'
"$PY" -B "$L568" s560pack "$W560P" "$WORK/walk_s560_pack_s568.py" > "$WORK/l560p.txt" 2>&1 || { cat "$WORK/l560p.txt"; die "the S560 pack walk's lines in S568's form (P2, P8) were not each found exactly once"; }
( cd "$WORK" && HOME="$WORK" "$PY" -B "$WORK/walk_s560_pack_s568.py" "$FIN/$PF" "$FIN" --before "$PK_BEFORE" > "$WORK/pack.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/pack.txt" | mask; die "the S560 pack walk is RED on the live packs.py"; }
grep -E 'pack checks' "$WORK/pack.txt" | tail -1 | sed 's/^/    S560 pack walk (P2 \/ P8 in S568'"'"'s form) on packs.py as it is (S601 does not touch it): /'
( cd "$WORK" && HOME="$WORK" "$PY" -B "$W548" "$FIN/$PF" "$FIN" > "$WORK/s548.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s548.txt" | mask; die "the S548 pack walk is RED"; }
grep -E 'checks' "$WORK/s548.txt" | tail -1 | sed 's/^/    S548 pack walk: /'
"$PY" -B "$L563" s559 "$W559" "$WORK/walk_s559_s563.py" > "$WORK/l559.txt" 2>&1 || { cat "$WORK/l559.txt"; die "the S559 walk's lines (S563's form) were not each found exactly once"; }
"$PY" -B "$L566" s559 "$WORK/walk_s559_s563.py" "$WORK/walk_s559_s566.py" > "$WORK/l559b.txt" 2>&1 || { cat "$WORK/l559b.txt"; die "the S559 walk's lines S566 changes were not each found exactly once"; }
( cd "$WORK" && "$PY" -B "$W559" "$WORK/live_in" "$WORK/snap.db" --work "$WORK/w7" --shared "$SHARED" --dump "$WORK/b559.json" > "$WORK/s559base.txt" 2>&1 ) || { tail -3 "$WORK/s559base.txt" | mask; die "the S559 walk's baseline could not be taken on the live files"; }
( cd "$WORK" && "$PY" -B "$WORK/walk_s559_s566.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w8" --shared "$SHARED" --baseline "$WORK/b559.json" --from-widget "$W559FROM" > "$WORK/s559.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s559.txt" | mask | cut -c1-400; die "the S559 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s559.txt" | tail -1 | sed 's/^/    S559 walk (J1 \/ J3 in S563'"'"'s form, O3 \/ O4 in S566'"'"'s; M1 unchanged) on the new files: /'
( cd "$WORK" && "$PY" -B "$W557" "$WORK/noam" "$WORK/snap.db" --work "$WORK/w9" --shared "$SHARED" --dump "$WORK/b557.json" > "$WORK/s557base.txt" 2>&1 ) || { tail -3 "$WORK/s557base.txt" | mask; die "the S557 walk's baseline could not be taken"; }
( cd "$WORK" && "$PY" -B "$W557" "$WORK/built" "$WORK/snap.db" --work "$WORK/w10" --shared "$SHARED" --baseline "$WORK/b557.json" > "$WORK/s557.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s557.txt" | mask | cut -c1-400; die "the S557 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s557.txt" | tail -1 | sed 's/^/    S557 walk on the new files: /'
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$W555" "$WORK/built" "$WORK/snap.db" --work "$WORK/w11" --shared "$SHARED" > "$WORK/s555.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s555.txt" | mask | cut -c1-400; die "the S555 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s555.txt" | tail -1 | sed 's/^/    S555 walk on the new files: /'
"$PY" -B "$L559" "$W551" "$WORK/walk_s551_s559.py" > "$WORK/s551lines.txt" 2>&1 || { cat "$WORK/s551lines.txt"; die "the S551 walk's three agreed lines (S559's) were not each found exactly once"; }
( cd "$WORK" && PYTHONPATH="$WORK/am" "$PY" -B "$WORK/walk_s551_s559.py" "$WORK/built" "$WORK/snap.db" --work "$WORK/w15" --shared "$SHARED" > "$WORK/s551.txt" 2>&1 ) || { grep -E '^RED|checks' "$WORK/s551.txt" | mask | cut -c1-400; die "the S551 walk is RED on the built files"; }
grep -E 'checks' "$WORK/s551.txt" | tail -1 | sed 's/^/    S551 walk (S559'"'"'s three agreed lines) on the new files: /'
if [ -n "${DRY:-}" ]; then echo "DRY=1: stopped before placing. $KIT: NOT INSTALLED (dry run; nothing written, no lock)"; exit 0; fi

log "the install-day state BEFORE (the live files on a fresh copy) and as the NEW files read the same copy"
copydb "$DB" "$WORK/state0.db" || die "the state's copy failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s601.py" --state "$WORK/live_in" "$WORK/state0.db" --work "$WORK/st_before" --shared "$SHARED" --label before 2>&1 ) | mask | grep -E '^STATE' | sed 's/^/    /'
copydb "$DB" "$WORK/state1.db" || die "the state's copy failed"
( cd "$WORK" && "$PY" -B "$HERE/walk_s601.py" --state "$WORK/built" "$WORK/state1.db" --work "$WORK/st_new" --shared "$SHARED" --label new 2>&1 ) | mask | grep -E '^STATE' | sed 's/^/    /'
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || die "the build lock is not held by $KIT -- nothing placed"

log "backups beside the live files, and the database by the backup API (BEFORE the restart and the data step)"
for f in $EDITED; do
  P="$(pin PIN_FROM_$(base "$f").txt)"
  cp -p "$APP/$f" "$APP/$f.bak_S601_${P:0:8}" || die "backup of $f failed"
  [ "$(md5 "$APP/$f.bak_S601_${P:0:8}")" = "$P" ] || die "the backup of $f is not the live file"
done
copydb "$DB" "$DB.bak_S601_$STAMP" && chmod 600 "$DB.bak_S601_$STAMP" || die "database backup failed"
echo "    asset_register.py.bak_S601_$(pin PIN_FROM_asset_register.txt | cut -c1-8) . claude_reread.py.bak_S601_$(pin PIN_FROM_claude_reread.txt | cut -c1-8) . $(basename "$DB").bak_S601_$STAMP ($(stat -c %s "$DB.bak_S601_$STAMP") bytes)"
declare -A NT0; for f in $READONLY; do NT0[$f]="$(md5 "$APP/$f")"; done; NT0[$SHRO]="$(md5 "$SHARED/$SHRO")"; NT0[$PF]="$(md5 "$FIN/$PF")"

restore(){
  echo "RESTORING $EDITED from their backups (one command), one restart"
  local pa pr
  pa="$(pin PIN_FROM_asset_register.txt)"; pr="$(pin PIN_FROM_claude_reread.txt)"
  \cp -p "$APP/asset_register.py.bak_S601_${pa:0:8}" "$APP/asset_register.py" && \cp -p "$APP/claude_reread.py.bak_S601_${pr:0:8}" "$APP/claude_reread.py"
  rm -f "$APP"/*.tmp_s601
  eval "$RESTART" || true
  [ "$(md5 "$APP/asset_register.py")" = "$pa" ] && [ "$(md5 "$APP/claude_reread.py")" = "$pr" ] || { echo "RESTORE FAILED -- run the UNDO line in the README"; exit 2; }
  RH=""; for i in $(seq 1 "$TRIES"); do sleep 2; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  [ "$RH" = "200" ] || { echo "RESTORED THE FILES, BUT THE SCAN APP DOES NOT ANSWER (${RH:-nothing}) -- tell Claude now"; exit 2; }
  echo "    both files back at their FROM pins (${pa:0:8}, ${pr:0:8}); healthz 200 after the restore; the setting read.sarvam was NOT written"
  echo "$KIT: NOT INSTALLED (restored; the database backup stays)"
  exit 1
}

log "place the two files (staged, then renamed in ONE command), and read the md5s back"
for f in $EDITED; do cp "$WORK/built/$f" "$APP/$f.tmp_s601" || die "could not stage $f"; [ "$(md5 "$APP/$f.tmp_s601")" = "$(pin PIN_TO_$(base "$f").txt)" ] || die "the staged $f is not at its pin"; done
PLACED=1
mv -f "$APP/asset_register.py.tmp_s601" "$APP/asset_register.py" && mv -f "$APP/claude_reread.py.tmp_s601" "$APP/claude_reread.py" || restore
for f in $EDITED; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base "$f").txt)" ] && cmp -s "$APP/$f" "$WORK/built/$f" || restore; done
for f in $READONLY; do [ "$(md5 "$APP/$f")" = "${NT0[$f]}" ] || restore; done
echo "    placed: $(for f in $EDITED; do printf '%s %s . ' "$f" "$(md5 "$APP/$f" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files); the read-only files unchanged"

log "restart $SERVICE (only), then health"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
eval "$RESTART" || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep 2; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ -n "${S601_FORCE_RED:-}" ] && { echo "    (rehearsal: a red after placing is forced)"; HC="forced-red"; }
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200 (restarted at $T0)"
for pg in admin bills; do
  X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/$pg")"; [ "$X" = "302" ] && break; sleep 2; done
  if [ "$X" = "302" ]; then echo "    /$pg answers 302 (the login gate -- expected, not a failure): mounted and gated"
  else echo "    /$pg answered ${X:-nothing}, not 302: it did not mount, or its login gate is open"; restore; fi
done
if command -v "$JOURNALCTL" >/dev/null 2>&1 && [ "$RESTART" != "true" ]; then
  "$JOURNALCTL" -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && { echo "    journal: a module NOT mounted"; restore; }
  JR="$("$JOURNALCTL" -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || { echo "    journal: $JR error line(s) since the restart"; restore; }
  echo "    journal clean since the restart"
fi

log "the data step: read.sarvam = off (one INSERT OR REPLACE on the live database; the owner's word)"
if [ -n "${S601_FORCE_DATA_RED:-}" ]; then echo "    (rehearsal: the data step is forced red, before it runs)"; restore; fi
SW="$("$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1], timeout=30); c.execute(\"INSERT OR REPLACE INTO settings(key,value) VALUES('read.sarvam','off')\"); c.commit(); print(c.execute(\"SELECT value FROM settings WHERE key='read.sarvam'\").fetchone()[0]); c.close()" "$DB" 2>&1)" || { echo "    the data step failed: $SW"; restore; }
[ "$SW" = "off" ] || { echo "    the setting read back '$SW', not 'off'"; restore; }
echo "    read.sarvam = $SW ($(date '+%Y-%m-%d %H:%M:%S'))"

log "the state AFTER (the live files, a fresh copy of the live database; the owner's card: Claude ON, Sarvam OFF), and nothing else moved"
copydb "$DB" "$WORK/state2.db" || restore
SA="$( cd "$WORK" && "$PY" -B "$HERE/walk_s601.py" --state "$APP" "$WORK/state2.db" --work "$WORK/st_after" --shared "$SHARED" --label after 2>&1 )"
echo "$SA" | mask | grep -E '^STATE' | sed 's/^/    /'
echo "$SA" | grep -q "^STATE OK S601 after" || { echo "    the state after could not be read"; restore; }
echo "$SA" | grep "the admin page as the owner" | grep -q "Claude: ON" || { echo "    the owner's card does not read Claude ON"; restore; }
echo "$SA" | grep "the admin page as the owner" | grep -q "Sarvam: OFF" || { echo "    the owner's card does not read Sarvam OFF"; restore; }
for f in $READONLY; do [ "$(md5 "$APP/$f")" = "${NT0[$f]}" ] || restore; done
[ "$(md5 "$SHARED/$SHRO")" = "${NT0[$SHRO]}" ] || restore
[ "$(md5 "$FIN/$PF")" = "${NT0[$PF]}" ] || restore
for f in $SANJ; do [ "$(md5 "$FIN/$f")" = "${SANJ0[$f]}" ] || restore; done
[ "$(crontab -l 2>/dev/null | md5sum | cut -c1-32)" = "$CRON0" ] || restore
[ "$(hc "$HEALTH")" = "200" ] || restore
echo "    the read-only files, sarvam_ocr.py, packs.py, the six Sanjeevni files and the crontab unchanged; healthz 200"

DONE=1
echo
echo "$KIT: DONE."
for f in $EDITED; do echo "  PINS (read back): $f $(md5 "$APP/$f")"; done
echo "  WHAT HIS PAGES NOW SHOW: his scan-app Admin page has the Claude card with the new words and, beside it, 'Reading the scans — Sarvam'"
echo "  reading Now: OFF with a Switch ON button. From the next real scan, Claude fills the pharmacy bills (supplier, bill number, date,"
echo "  total and the item lines) as it fills the clinic's papers; a paper it cannot read is tried again three times over two hours."
echo "  Nothing on any staff page changes."
echo "  THE LOCK: $LOCK stays held by $KIT until the report is written (then: rm -rf $LOCK)."
echo "  UNDO (one line): \\cp -p $APP/asset_register.py.bak_S601_$(pin PIN_FROM_asset_register.txt | cut -c1-8) $APP/asset_register.py && \\cp -p $APP/claude_reread.py.bak_S601_$(pin PIN_FROM_claude_reread.txt | cut -c1-8) $APP/claude_reread.py && systemctl restart $SERVICE"
echo "  (the setting read.sarvam stays 'off' after an undo -- the old file ignores it; the owner's card is the door to switch it on)"
exit 0
