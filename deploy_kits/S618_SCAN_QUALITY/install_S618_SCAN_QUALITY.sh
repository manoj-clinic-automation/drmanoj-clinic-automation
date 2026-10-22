#!/bin/bash
# =============================================================================
#  install_S618_SCAN_QUALITY.sh · kit S618 (22-Oct-2026) · brief claude_code_briefs/S618_SCAN_QUALITY.md (v2, Sanjeevni session 335)
#  Every pharmacy bill saved the right way up; the phone stops a badly blurred photo; "Scans to redo" for the owner and Shavez; a scan sent
#  back lands on reception's home as "Phir se scan karo"; the rescan replaces the old scan everywhere (the old one kept, set aside).
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S618_SCAN_QUALITY), 08:02-23:49 IST only:
#    rm -rf /tmp/s618kit && cp -rp <kit> /tmp/s618kit && bash /tmp/s618kit/install_S618_SCAN_QUALITY.sh
#  (DRY=1 before bash: every gate, the live facts, the scratch sides and every walk; nothing written on live, no lock, no wait.
#   QUICK=1 with DRY=1: S618's own walk only -- a builder's rehearsal; never for the install.)
#
#   /root/assetapp/asset_register.py  f29ee515 -> TO  rescan_of, scan_lie, the rescan in _create_intake_bill, blur_kept, _s618_lie after the reading
#   /root/assetapp/scanner_widget.js  10a8bb29 -> TO  the blur refusal (OpenCV path), blur_kept, arOK / guideRect read CFG at call time
#   /root/assetapp/claude_reader.py   3894dc23 -> TO  check_scan, turn_file, lie_pass, LIE_DDL (read() unchanged)
#   /root/finance/porders_s454.py     34bab464 -> TO  rescan_list, Scans to redo, Phir se scan karo, the ask and its withdraw, counts' rescan
#   /root/finance/order_sheet.py      c7fe2561 -> TO  scan_rescan_ask (DDL), pharmacy_scans' rescan_of, _s618_follow before tie_pass's loop
#   /root/shared/scan_quality.py      (new)    -> TO  the one rule and the one table of words
#  assets.db: bills.rescan_of and scan_lie by the app's own init_db at the restart; finance.db: scan_rescan_ask by OS.ensure. No DELETE, no hand
#  edit. Live data written by the kit: the backfill (scan_lie rows; a turned scan's source_stored by compare-and-set; one bill_audit 'upright').
#  ORDER: gates -> the lock -> the FROM pins, the read-only md5s -> pypdf / Pillow under both pythons -> the spine green -> the live facts BEFORE
#  -> the wait (no scan saved in the last 5 minutes; 30 minutes at most) -> build from the live bytes -> compile (both pythons) -> scratch: both
#  databases by the backup API, the two app folders twice (OLD / NEW) -> walk_s618 OLD (red) then NEW -> walk_s613 and S605's three walks OLD
#  vs NEW -> DRY stops -> backups -> DOCTOR_AUTO_OFF -> place (one command) -> md5 read back -> restart assetapp, its init_db, healthz -> restart
#  clinic-finance, healthz 200, the pages 302 -> journal clean -> the backfill on live -> the live facts AFTER -> nothing else moved -> off-switch
#  removed. Red after placing: the files back from their .bak_S618_<from8> (scan_quality.py moved aside), both restarts, healthz; a turned
#  scan's source_stored put back from its 'upright' audit only where it still names the turned file. The new column and tables stay, unread.
#  Under set -u, not set -e: every gate is a test. The lock stays held until the report is written.
# =============================================================================
set -u
KIT="S618_SCAN_QUALITY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
AR="${AR:-/root/assetapp}"
FIN="${FIN:-/root/finance}"
SHD="${SHD:-/root/shared}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-$AR/assets.db}"
DB="${DB:-$FIN/finance.db}"
UPL="${UPL:-$AR/uploads}"
REPO="${REPO:-/root/deploy/repo}"
BRIEFS="$REPO/claude_code_briefs"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
K605="$REPO/deploy_kits/S605_ORDER_FIXES"
K613="$REPO/deploy_kits/S613_S605_FOLLOWUP"
S603KIT="$REPO/deploy_kits/S603_AMIR_CALENDAR_SAFE"
S598KIT="$REPO/deploy_kits/S598_ARRIVALS_BY_LINE"
ROWS598="$FIN/purchase_order_line.bak_S598_20261019_095314.json"
OLD605="$SPN/spine_build.py.bak_S605_e3d3ed85"; OLD605_MD5=e3d3ed85973eab2df0326dc9621e230e
DUTY_V17=ef42b15568f681b1942abcc6639bec57
LABELS="$KDIR/S335_SCAN_VISUAL_AUDIT.json"
AR_PORT="${AR_PORT:-8030}"; FIN_PORT="${FIN_PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EAR="asset_register.py scanner_widget.js claude_reader.py"
EFIN="porders_s454.py order_sheet.py"
declare -A FROM TO READ PRINT
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s618_inst_$STAMP"
PLACED=0; BACKFILLED=0
DBBAK="$FIN/finance.db.bak_S618_$STAMP"; ADBBAK="$AR/assets.db.bak_S618_$STAMP"; UPLIST="$AR/uploads_list.bak_S618_$STAMP.txt"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
home() { case "$1" in porders_s454.py|order_sheet.py) echo "$FIN";; scan_quality.py) echo "$SHD";; *) echo "$AR";; esac; }
live() { echo "$(home "$1")/$1"; }
bak() { echo "$(live "$1").bak_S618_${FROM[$1]:0:8}"; }
stg() { echo "$(home "$1")/.$1.s618"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" "$K605" "$K613" "$S603KIT" "$S598KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$1$2"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
sqlro() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); [print('   ', *[str(x) for x in r]) for r in c.execute(sys.argv[2]).fetchall()]" "$1" "$2" 2>&1 | mask; }
kits5() { ( cd "$REPO/deploy_kits" && find S5* S6* -type f ! -path '*/__pycache__/*' ! -path 'S618_SCAN_QUALITY/*' -print0 2>/dev/null | sort -z | xargs -0 md5sum | md5sum | awk '{print $1}' ); }
release_lock() { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back from their .bak_S618_* in one command"
  for n in $EAR $EFIN; do \cp -p "$(bak "$n")" "$(live "$n")" || say "   !! could not put back $n"; done
  [ -f "$SHD/scan_quality.py" ] && mv -f "$SHD/scan_quality.py" "$SHD/scan_quality.py.removed_S618_$STAMP"
  rm -f "$AR"/.*.s618 "$FIN"/.*.s618 "$SHD"/.*.s618
  if [ "$BACKFILLED" = 1 ]; then
    say "   the turned scans put back where source_stored still names the turned file (a later join kept):"
    "$APY" - "$ADB" <<'PYEOF' 2>&1 | sed 's/^/     /'
import json, sqlite3, sys
c = sqlite3.connect(sys.argv[1], timeout=60)
n = 0
for bid, d in c.execute("SELECT bill_id, detail FROM bill_audit WHERE action='upright' AND who LIKE 'server (S618%' ORDER BY id DESC").fetchall():
    try:
        j = json.loads(d)
    except ValueError:
        continue
    n += c.execute("UPDATE bills SET source_stored=? WHERE id=? AND source_stored=?", (j.get("from"), bid, j.get("to"))).rowcount
c.commit()
print("put back: %d" % n)
PYEOF
  fi
  "$SYSTEMCTL" restart assetapp || true; "$SYSTEMCTL" restart clinic-finance || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health "$FIN_PORT" /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EAR $EFIN; do say "   $(live "$n") $(m5 "$(live "$n")") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h, assetapp /login $(health "$AR_PORT" /login); the database backups stay: $DBBAK, $ADBBAK"
  rm -f "$OFFSW"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab diff pdftoppm pdfimages pdfinfo xargs; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"
{ { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/12] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for n in $EAR $EFIN; do [ -f "$(live "$n")" ] || { say "!! [1/12] $(live "$n") is not there - nothing installed"; exit 1; }; done
[ -d "$SHD" ] && [ -d "$UPL" ] && [ -f "$LABELS" ] || { say "!! [1/12] $SHD, $UPL or the labels file is missing - nothing installed"; exit 1; }
DM5="$(m5 "$BRIEFS/DUTY_MAP.json")"
[ "$DM5" = "$DUTY_V17" ] || [ "$DM5" = "$(m5 "$KDIR/DUTY_MAP.json")" ] || { say "!! [1/12] the clone's DUTY_MAP.json is $DM5: neither v17 nor this kit's v18 - nothing installed"; exit 1; }
[ "$(m5 "$K605/DUTY_MAP.json")" = "$DUTY_V17" ] || { say "!! [1/12] S605's DUTY_MAP.json (v17, read by S613's walk) is not at its md5 - nothing installed"; exit 1; }
ALL_TO=1; for n in $EAR $EFIN scan_quality.py; do [ "$(m5 "$(live "$n")")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the six files are the kit's. Nothing written. healthz $(health "$FIN_PORT" /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, the labels, DUTY_MAP v17 or v18, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi
stop_unlocked() { say "$1"; [ "${DRY:-0}" = 1 ] || release_lock; exit "${2:-1}"; }

for n in $EAR $EFIN; do C="$(m5 "$(live "$n")")"; [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/12] $(live "$n") is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; done
[ -e "$SHD/scan_quality.py" ] && stop_unlocked "!! [2/12] $SHD/scan_quality.py already exists (not this kit's) - STOP, nothing installed"
say "[2/12] live pins exact: $(for n in $EAR $EFIN; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)scan_quality.py absent (new)"
say "       the read-only files' live md5s (the brief, section 1):"
for f in "${!READ[@]}"; do C="$(m5 "$f")"; say "         $f $C"; [ "$C" = "${READ[$f]}" ] || stop_unlocked "!! [2/12] $f is $C, not ${READ[$f]} - this kit was built reading it: STOP, nothing installed"; done
for f in "${!PRINT[@]}"; do say "         $f $(m5 "$f") (printed; the brief pins it to nothing; at the build ${PRINT[$f]:0:8})"; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] && [ -f "$POR/tile_grants.json" ] || stop_unlocked "!! [2/12] a database, the spine or the portal is missing - nothing installed"
CRONN="$(crontab -l 2>/dev/null | wc -l | awk '{print $1}')"
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
[ "$SP_OK" = True ] && [ "$SP_GATE" = "13/13" ] && [ "$SP_AGE" -le 30 ] \
  || stop_unlocked "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - nothing installed" 4
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json"); for f in "${!READ[@]}"; do NOTT+=("$f"); done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"; KITS0="$(kits5)"
say "       the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); the crontab $CRONN lines; the published S5*/S6* kit folders hashed (${KITS0:0:8})"
say "       the board's PLANNED lines: read by the runner on the PC before this install (the board is not on this box)"
say "       pypdf / Pillow, each python (the turn uses them in the process when they import, else the venv python as a subprocess):"
for py in "$APY" "$VPY"; do
  say "         $py: $("$py" -c "
r=[]
for m in ('pypdf','PIL'):
    try:
        x=__import__(m); r.append('%s %s'%(m,getattr(x,'__version__','?')))
    except Exception:
        r.append('%s MISSING'%m)
print(', '.join(r))" 2>&1)"
done
"$VPY" -c "import pypdf, PIL" 2>/dev/null || stop_unlocked "!! [2/12] the venv python has no pypdf or Pillow -- the server could not turn a page: nothing installed"

mkdir -p "$SCR/built" "$SCR/shared_live" || stop_unlocked "!! cannot make $SCR - nothing installed"
export PYTHONDONTWRITEBYTECODE=1
facts() { ( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s618.py" --facts --label "$1" --adb "$ADB" --db "$DB" --shared "$2" 2>&1 ) | mask; }
cp -p "$KDIR/scan_quality.py" "$SCR/shared_live/"
say "[2/12] the live facts BEFORE (read only; the kit's scan_quality judges):"
FB="$(facts before "$SCR/shared_live")"; echo "$FB" | sed 's/^/ /'
echo "$FB" | grep -q "^FACTS OK S618 (before)" || stop_unlocked "!! [2/12] the live facts could not be read - nothing installed"

# ---- the wait: no scan saved in the last 5 minutes (30 minutes at most, every 2; still busy -> STOP)
busy() { "$APY" -c "import sqlite3,sys,datetime as d; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); t=(d.datetime.utcnow()-d.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'); print(c.execute('SELECT COUNT(*) FROM bills WHERE created_at>=?', (t,)).fetchone()[0])" "$ADB" 2>/dev/null || echo 1; }
if [ "${DRY:-0}" = 1 ]; then
  say "       the wait: DRY RUN -- not waited ($(busy) scan(s) saved in the last 5 minutes now)"
else
  W0="$(TZ=Asia/Kolkata date '+%H:%M:%S')"; WAITED=0
  while [ "$(busy)" != 0 ] && [ "$WAITED" -lt 30 ]; do say "       $(TZ=Asia/Kolkata date '+%H:%M:%S IST'): $(busy) scan(s) saved in the last 5 minutes -- waiting 2 minutes"; sleep 120; WAITED=$((WAITED+2)); done
  [ "$(busy)" = 0 ] || stop_unlocked "!! the wait: 30 minutes from $W0 IST and the Scan App is still busy -- STOP; the lock released, nothing installed"
  say "       the wait: from $W0 IST, $WAITED minute(s) -- no scan saved in the last 5 minutes at $(TZ=Asia/Kolkata date '+%H:%M:%S IST')"
fi

for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s618.py walk_s618.py backfill_s618.py scan_quality.py || stop_unlocked "!! [3/12] compile failed on $py - nothing installed"
done
"$APY" -B make_s618.py --assetapp "$AR" --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { mask < "$SCR/make.txt"; stop_unlocked "!! [4/12] the builder refused a live file - nothing installed"; }
for n in $EAR $EFIN scan_quality.py; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; done
for py in "$APY" "$VPY"; do
  for n in asset_register.py claude_reader.py porders_s454.py order_sheet.py scan_quality.py; do
    PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || stop_unlocked "!! [3/12] the built $n does not compile on $py - nothing installed"
  done
done
say "[3/12] the kit's python files and the five built python files compile on $APY and $VPY; scanner_widget.js: no node on this box -- V8 parsed the"
say "       same bytes (${TO[scanner_widget.js]:0:8}) in the PC's headless Chrome (walk/walk_results_s618.txt, check V)"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each at its TO pin"

# ---- 5: the scratch sides
copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine_live.db" || stop_unlocked "!! [5/12] no copy of the databases - nothing installed"
mkdir -p "$SCR/uploads0"
"$APY" -c "
import sqlite3,sys,shutil,os
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
n=0
for (f,) in c.execute(\"SELECT source_stored FROM bills WHERE lane='pharmacy' AND substr(created_at,1,10)>='2026-10-08' AND source_stored IS NOT NULL\"):
    p=os.path.join(sys.argv[2],f)
    if os.path.exists(p):
        shutil.copy2(p,os.path.join(sys.argv[3],f)); n+=1
print(n)" "$SCR/base_a.db" "$UPL" "$SCR/uploads0" > "$SCR/nup.txt" || stop_unlocked "!! [5/12] the scans could not be copied to scratch - nothing installed"
mkar() {   # $1 side: the Scan App folder, the shared folder, the portal, the databases, the uploads
  local d="$SCR/$1"; mkdir -p "$d/assetapp/static" "$d/shared" "$d/portal" "$d/uploads"
  cp -p "$AR"/*.py "$AR"/*.js "$d/assetapp/" 2>/dev/null; cp -p "$AR"/static/opencv.js* "$d/assetapp/static/" 2>/dev/null
  cp -p "$SHD"/*.py "$d/shared/" 2>/dev/null
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$d/portal/"; done
  cp -p "$POR/tile_grants.json" "$d/portal/" || return 1; cp -rp "$POR/forms" "$d/portal/" 2>/dev/null
  cp -p "$SCR/uploads0"/* "$d/uploads/" || return 1
  cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/base.db" "$d/f.db"
}
mkfin() {   # S613's mkside: the finance folder, marg_ingest, a portal copy per walk, the databases
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive" "$d/marg_ingest/lib"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -p "$MARG"/lib/*.py "$d/marg_ingest/lib/" 2>/dev/null
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  for x in por613 por605 por603; do mkdir -p "$d/$x" && cp -rp "$d/portal/." "$d/$x/"; done
  for x in f613 f605 f603 f598; do cp -p "$SCR/base.db" "$d/$x.db" || return 1; done
  cp -p "$SCR/spine_live.db" "$d/finance/spine/spine.db"
}
for side in new old; do rm -rf "$SCR/$side"; { mkar "$side" && mkfin "$side"; } || stop_unlocked "!! [5/12] no scratch side '$side' - nothing installed"; done
for n in $EAR; do cp -p "$SCR/built/$n" "$SCR/new/assetapp/$n"; done
for n in $EFIN; do cp -p "$SCR/built/$n" "$SCR/new/finance/$n"; done
cp -p "$SCR/built/scan_quality.py" "$SCR/new/shared/scan_quality.py"
say "[5/12] scratch: both databases and the spine by the backup API; the Scan App, /root/shared and the finance folder twice -- NEW (the six built"
say "       files) and OLD (as they are); the $(cat "$SCR/nup.txt") pharmacy-lane scans since 08-Oct copied to each side's own uploads; a portal copy per walk"

# ---- 6: the walks
w618() { ( cd /tmp && timeout 5400 "$APY" -B "$KDIR/walk_s618.py" --ar "$SCR/$1/assetapp" --fin "$SCR/$1/finance" --shared "$SCR/$1/shared" --adb "$SCR/$1/a.db" \
          --db "$SCR/$1/f.db" --uploads "$SCR/$1/uploads" --por "$SCR/$1/portal" --duty-map "$KDIR/DUTY_MAP.json" --labels "$LABELS" --kit "$KDIR" --vpy "$VPY" \
          --dump "$SCR/dump_$1" "${@:2}" 2>&1 ); }
ROUT="$(w618 old --expect-red)"; RRC=$?
WOUT="$(w618 new --old-dump "$SCR/dump_old")"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
cp -p "$SCR/dump_new/intake_new.html" "$SCR/dump_old/intake_old.html" "${KEEPDIR:-/tmp}/" 2>/dev/null
[ "$WRC" = 0 ] && echo "$WOUT" | grep -q "^WALK OK S618" || stop_unlocked "!! [6/12] walk_s618 is RED on this box (exit $WRC) - nothing installed"
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  red: |^  NOT RED|^WALK OK negative|^NEGATIVE CONTROL|^WALK RED" | sed 's/^/   /'
[ "$RRC" = 0 ] && echo "$ROUT" | grep -q "^WALK OK negative control S618" || { echo "$ROUT" | mask | tail -30; stop_unlocked "!! [6/12] the negative control did not go red on the old files - nothing installed"; }
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S618: //')"
if [ "${QUICK:-0}" = 1 ] && [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN (QUICK): S618's walk only; NOTHING written"; exit 0; fi
# walk_s613 and S605's three walks on the OLD (live) and the NEW side: their check lines must be equal (this kit changes nothing they check)
d="$SCR/sp_old605"; mkdir -p "$d"; cp -p "$SPN/spine_read.py" "$d/"; cp -p "$OLD605" "$d/spine_build.py"
[ "$(m5 "$OLD605")" = "$OLD605_MD5" ] || stop_unlocked "!! [6/12] S605's OLD spine builder is not at its md5 - nothing installed"
( cd "$d" && timeout 1200 "$VPY" -B spine_build.py --readings "$SPN/readings" --rules "$SPN/spine_rules.json" --out "$d/spine.db" --finance-db "$SCR/base.db" > "$d/build.txt" 2>&1 )
grep -q "^SPINE BUILT" "$d/build.txt" || stop_unlocked "!! [6/12] S605's OLD builder did not build a scratch spine - nothing installed"
w613() { ( cd /tmp && timeout 2400 "$APY" -B "$K613/walk_s613.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f613.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por613" \
          --duty-map "$K605/DUTY_MAP.json" --spine-old605 "$SCR/sp_old605/spine.db" --dump "$SCR/d613_$1" 2>&1 ); }
w605() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s605.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f605.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por605" --duty-map "$K605/DUTY_MAP.json" --dump "$SCR/d605_$1" 2>&1 ); }
w603() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s603.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f603.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por603" --duty-map "$S603KIT/DUTY_MAP.json" --dump "$SCR/d603_$1" 2>&1 ); }
w598() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s598.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f598.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --kit "$S598KIT" --rows-json "$ROWS598" --dump "$SCR/d598_$1" 2>&1 ); }
wlines() { grep -E '^  (ok|FAIL) ' | sed -E 's/   \[.*$//; s/[0-9]+\.[0-9]+s/N.Ns/g; s/[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?/HH:MM/g; s/\(200, [0-9]+ bytes\)/(200, N bytes)/; s/[0-9]{10,}/##########/g'; }
for w in 613 605 603 598; do
  for side in old new; do cp -p "$SCR/base_a.db" "$SCR/$side/a.db"; done                   # S613's and S605's walks read a quiet assets copy
  O="$(w$w old)"; ORC=$?; N="$(w$w new)"; NRC=$?
  echo "$O" | wlines > "$SCR/w${w}_old.txt"; echo "$N" | wlines > "$SCR/w${w}_new.txt"
  say "       walk_s$w -- on the OLD (live) files: $(echo "$O" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $ORC); on the NEW files: $(echo "$N" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $NRC)"
  [ -s "$SCR/w${w}_new.txt" ] || stop_unlocked "!! [6/12] walk_s$w printed no check line - nothing installed"
  diff "$SCR/w${w}_old.txt" "$SCR/w${w}_new.txt" | grep -E '^[<>] ' > "$SCR/w${w}_diff.txt"
  if [ -s "$SCR/w${w}_diff.txt" ]; then
    say "         its check lines that differ, both ways (< OLD, > NEW):"; mask < "$SCR/w${w}_diff.txt" | cut -c1-230 | sed 's/^/           /'
    stop_unlocked "!! [6/12] walk_s$w differs OLD vs NEW -- this kit must change nothing it checks: nothing installed"
  fi
  say "         every check line equal OLD vs NEW ($(wc -l < "$SCR/w${w}_new.txt") lines)"
  grep '^  FAIL ' "$SCR/w${w}_old.txt" | cut -c1-200 | sed 's/^/         red on both sides (the live day, not this kit): /'
done
find "$KDIR" "$K605" "$K613" "$S603KIT" "$S598KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for n in $EAR $EFIN; do [ "$(m5 "$(live "$n")")" = "${FROM[$n]}" ] || stop_unlocked "!! [6/12] $(live "$n") changed during the walks - nothing installed"; done
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the live facts, the scratch sides and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 7: backups
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; stop_unlocked "!! [7/12] finance.db backup failed - nothing placed"; }
copydb "$ADB" "$ADBBAK" && chmod 600 "$ADBBAK" || { rm -f "$ADBBAK"; stop_unlocked "!! [7/12] assets.db backup failed - nothing placed"; }
ls -la --time-style=full-iso "$UPL" > "$UPLIST" || stop_unlocked "!! [7/12] the uploads list could not be written - nothing placed"
for n in $EAR $EFIN; do
  \cp -p "$(live "$n")" "$(bak "$n")" || stop_unlocked "!! [7/12] backup of $n failed - nothing placed"
  [ "$(m5 "$(bak "$n")")" = "${FROM[$n]}" ] || stop_unlocked "!! [7/12] the backup of $n is not the live file - nothing placed"
done
say "[7/12] backups: $(basename "$DBBAK") ($(stat -c %s "$DBBAK") bytes), $(basename "$ADBBAK") ($(stat -c %s "$ADBBAK") bytes), both by the sqlite backup API;"
say "       $(basename "$UPLIST") ($(($(wc -l < "$UPLIST") - 3)) files); $(for n in $EAR $EFIN; do printf '%s ' "$(basename "$(bak "$n")")"; done)"

# ---- 8-9: the files in ONE move; assetapp restarted, then clinic-finance
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restarts below are this kit's; S578 must not restart a part it finds down" > "$OFFSW" || stop_unlocked "!! [8/12] could not write $OFFSW - nothing placed"
for n in $EAR $EFIN scan_quality.py; do
  { if [ -f "$(live "$n")" ]; then \cp -p "$(live "$n")" "$(stg "$n")"; else : > "$(stg "$n")"; chmod 644 "$(stg "$n")"; fi; } && cat "$SCR/built/$n" > "$(stg "$n")" && [ "$(m5 "$(stg "$n")")" = "${TO[$n]}" ] \
    || { rm -f "$AR"/.*.s618 "$FIN"/.*.s618 "$SHD"/.*.s618 "$OFFSW"; stop_unlocked "!! [8/12] could not stage $n - nothing placed"; }
done
PLACED=1
MV=""; for n in $EAR $EFIN scan_quality.py; do MV="$MV mv -f '$(stg "$n")' '$(live "$n")' &&"; done
eval "${MV% &&}" || restore "placing the files"
for n in $EAR $EFIN scan_quality.py; do [ "$(m5 "$(live "$n")")" = "${TO[$n]}" ] && cmp -s "$(live "$n")" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[8/12] placed by rename in ONE command; md5 read back: $(for n in $EAR $EFIN scan_quality.py; do printf '%s %s . ' "$n" "$(m5 "$(live "$n")" | cut -c1-8)"; done)(= the TO pins, byte-identical to the walked files)"
TA="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart assetapp || restore "restart assetapp"
a1=000; for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; a1=$(health "$AR_PORT" /login); [ "$a1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet assetapp || restore "assetapp is not active"
[ "$a1" = 200 ] || restore "assetapp /login $a1"
a2=$(health "$AR_PORT" /intake); [ "$a2" = 302 ] || restore "assetapp /intake answered $a2 without a login (302 = the login gate, expected)"
INIT="$("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print('rescan_of' in [r[1] for r in c.execute('PRAGMA table_info(bills)')], bool(c.execute(\"SELECT 1 FROM sqlite_master WHERE name='scan_lie'\").fetchone()))" "$ADB" 2>&1)"
[ "$INIT" = "True True" ] || restore "assetapp's init_db did not make bills.rescan_of and scan_lie ($INIT)"
say "[9/12] assetapp restarted at $TA (the box's clock) and active -- /login $a1, /intake $a2 without a login (the login gate, expected); its init_db made bills.rescan_of and scan_lie"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart clinic-finance || restore "restart clinic-finance"
c1=000; for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health "$FIN_PORT" /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet clinic-finance || restore "clinic-finance is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FIN_PORT" /finance/porders); c3=$(health "$FIN_PORT" /finance/porders/s454/scans); c4=$(health "$FIN_PORT" /finance/porders/s454/rescan); c5=$(health "$FIN_PORT" /finance/porders/s454/order)
for c in "$c2" "$c3" "$c4" "$c5"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): porders $c2 / s454/scans $c3 / s454/rescan $c4 / s454/order $c5";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$( { "$JOURNALCTL" -u clinic-finance --since "$T0" --no-pager; "$JOURNALCTL" -u assetapp --since "$TA" --no-pager; } 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restarts"
fi
say "        clinic-finance restarted at $T0 (the box's clock) and active - healthz $c1 - /finance/porders $c2, /s454/scans $c3, /s454/rescan $c4, /s454/order $c5"
say "        without a login (302 = the login gate, expected) - journal clean (both services); nothing else restarted"

# ---- 10: the backfill on live; the state AFTER; DUTY_MAP's due_sql on live
say "[10/12] the backfill on live (the venv python; claude_reader.lie_pass, the Scan App's own call):"
BACKFILLED=1
BF="$( cd /tmp && timeout 3600 "$VPY" -B "$KDIR/backfill_s618.py" --assetapp "$AR" --adb "$ADB" --uploads "$UPL" 2>&1 )"; BRC=$?
echo "$BF" | mask | sed 's/^/   /'
echo "$BF" | grep -q "^BACKFILL S618: [0-9]* scans" || restore "the backfill did not run (exit $BRC)"
BF2="$( cd /tmp && timeout 600 "$VPY" -B "$KDIR/backfill_s618.py" --assetapp "$AR" --adb "$ADB" --uploads "$UPL" 2>&1 | tail -1 )"
say "        a second run: $BF2"
say "        the live facts AFTER (read only):"
FA="$(facts after "$SHD")"; echo "$FA" | sed 's/^/ /'
echo "$FA" | grep -q "^FACTS OK S618 (after)" || restore "the live facts after placing could not be read"
for _t in $(seq 1 30); do sqlro "$DB" "SELECT 1 FROM sqlite_master WHERE name='scan_rescan_ask'" | grep -q 1 && break; sleep 10; done
say "        DUTY_MAP reception.rescan's due_sql on live (read only): $(sqlro "$DB" "$("$APY" -c "import json,sys; print([d for d in json.load(open(sys.argv[1]))['duties'] if d['id']=='reception.rescan'][0]['due_sql'])" "$KDIR/DUTY_MAP.json")" | tr -s ' ')"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(kits5)" = "$KITS0" ] || restore "a published S5*/S6* kit folder moved"
[ "$(health "$FIN_PORT" /finance/healthz)" = 200 ] || restore "healthz at the end"
PLACED=0
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, portal.py, tile_grants.json, the crontab, the published kit folders); healthz 200; $OFFSW removed"

# ---- 11: md5 read back
say "[11/12] md5 read back:"
for n in $EAR $EFIN scan_quality.py; do md5sum "$(live "$n")"; done
find "$AR" "$FIN" "$SHD" -maxdepth 1 -newer "$SCR/make.txt" -name '__pycache__' 2>/dev/null | head -3 | sed 's/^/        (a python cache folder refreshed by the services: /;s/$/)/'
say "[12/12] $KIT: DONE. The build lock stays held by $KIT until the report is written (release: rm -f $LOCK/owner; rmdir $LOCK)."
say "undo (the files): $(for n in $EAR $EFIN; do printf '\\cp -p %s %s && ' "$(bak "$n")" "$(live "$n")"; done)mv $SHD/scan_quality.py $SHD/scan_quality.py.undone && $SYSTEMCTL restart assetapp clinic-finance"
exit 0
