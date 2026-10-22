#!/bin/bash
# =============================================================================
#  install_S619_ORDER_TRACKER.sh · kit S619 (22-Oct-2026) · brief claude_code_briefs/S619_ORDER_TRACKER.md (v2, Sanjeevni session 335)
#  One order, five steps, the same on every screen (order_track): reception's call row 'Order ka maal nahi aaya -- call karo' (late = two days,
#  Sunday not counted, 18:00; part orders too); a medicine that did not come goes on that dealer's next order by itself (order_carry); a reason
#  on the one remove door; Darpan's one line; the order list for the owner and Shavez; the WhatsApp's delivery line and the papers'.
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S619_ORDER_TRACKER), 08:02-23:49 IST only:
#    rm -rf /tmp/s619kit && cp -rp <kit> /tmp/s619kit && bash /tmp/s619kit/install_S619_ORDER_TRACKER.sh
#  (DRY=1 before bash: every gate, the live facts, the scratch sides and every walk; nothing written on live, no lock, no wait.
#   QUICK=1 with DRY=1: S619's own walk only -- a builder's rehearsal; never for the install.)
#
#   /root/finance/order_sheet.py      ff9375f9 -> TO  settings, order_carry + reason (ensure), the tie's asking, the carry on the cards, wa_body
#   /root/finance/porders_s454.py     4d150648 -> TO  the call row and its page, Maal aaya, the order list, the reason chips, the owner's card
#   /root/finance/darpan_kal.py       d6ba4882 -> TO  the day payload's order line; his order tab reads order_track
#   /root/finance/darpan_kal.html     c0ddc0ea -> TO  orderTrackSec after 'Aaj ke order'
#   /root/finance/order_sheet_pdf.py  7a6d47c0 -> TO  the delivery line in the foot; carried / dealer_no rows
#   /root/finance/marg_order_pdf.py   bdcf2d00 -> TO  the delivery line once after Marg's last row
#   /root/finance/order_track.py      (new)    -> TO  the one reader
#  finance.db: table order_carry and s454_line_edit.reason by order_sheet.ensure (guarded); five settings by INSERT OR IGNORE; the first carry
#  pass (order_track.carry_pass, keyed by line). No DELETE, no hand edit. Service clinic-finance, restarted once.
#  ORDER: gates -> the lock -> the FROM pins, the read-only md5s -> the spine green -> build from the live bytes -> the live facts BEFORE (a
#  backup-API copy; SELECT and a read-only Ctx, never a page) -> the wait (no order message queued, none handed in the last 10 minutes; 30
#  minutes at most) -> compile (both pythons) -> scratch: the databases by the backup API, the finance folder twice (OLD / NEW) -> walk_s619 OLD
#  (red) then NEW -> walk_s618 / walk_s613 / S605's three walks OLD vs NEW (a NEW red line must be one this kit changes on purpose) -> DRY stops
#  -> backups -> DOCTOR_AUTO_OFF -> place (one command) -> md5 read back -> the table and the column (order_sheet.ensure) -> one restart ->
#  healthz 200, the pages 302 -> journal clean -> the first carry pass -> the facts AFTER, the duty map's SQL on live -> nothing else moved ->
#  off-switch removed. Red after placing: the files back from their .bak_S619_<from8> (order_track.py moved aside), one restart, healthz; the
#  new table and column stay, unread. Under set -u, not set -e: every gate is a test. The lock stays held until the report is written.
# =============================================================================
set -u
KIT="S619_ORDER_TRACKER"
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
K618="$REPO/deploy_kits/S618_SCAN_QUALITY"
S603KIT="$REPO/deploy_kits/S603_AMIR_CALENDAR_SAFE"
S598KIT="$REPO/deploy_kits/S598_ARRIVALS_BY_LINE"
ROWS598="$FIN/purchase_order_line.bak_S598_20261019_095314.json"
OLD605="$SPN/spine_build.py.bak_S605_e3d3ed85"; OLD605_MD5=e3d3ed85973eab2df0326dc9621e230e
DUTY_V18=21ca346d0b89bd10d9cbb7600c7f5fa0
FIN_PORT="${FIN_PORT:-8106}"; AR_PORT="${AR_PORT:-8030}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EFIN="order_sheet.py porders_s454.py darpan_kal.py darpan_kal.html order_sheet_pdf.py marg_order_pdf.py"
NEWF="order_track.py"
# the lines of the earlier walks this kit changes ON PURPOSE (brief 4.9): S605's call row (retired: the late row), S618's 'Scans to redo' link (the order list's card)
ALLOW="the owner's home links 'Scans to redo: N' while there is any|C: \(3\) the call row counts today's orders still awaited"
declare -A FROM TO READ PRINT
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s619_inst_$STAMP"
PLACED=0
DBBAK="$FIN/finance.db.bak_S619_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
live() { echo "$FIN/$1"; }
bak() { echo "$(live "$1").bak_S619_${FROM[$1]:0:8}"; }
stg() { echo "$FIN/.$1.s619"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" "$K605" "$K613" "$K618" "$S603KIT" "$S598KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$1$2"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
sqlro() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); [print('   ', *[str(x) for x in r]) for r in c.execute(sys.argv[2]).fetchall()]" "$1" "$2" 2>&1 | mask; }
kits5() { ( cd "$REPO/deploy_kits" && find S5* S6* -type f ! -path '*/__pycache__/*' ! -path 'S619_ORDER_TRACKER/*' -print0 2>/dev/null | sort -z | xargs -0 md5sum | md5sum | awk '{print $1}' ); }
release_lock() { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back from their .bak_S619_* in one command"
  for n in $EFIN; do \cp -p "$(bak "$n")" "$(live "$n")" || say "   !! could not put back $n"; done
  [ -f "$FIN/order_track.py" ] && mv -f "$FIN/order_track.py" "$FIN/order_track.py.removed_S619_$STAMP"
  rm -f "$FIN"/.*.s619
  "$SYSTEMCTL" restart clinic-finance || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health "$FIN_PORT" /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EFIN; do say "   $(live "$n") $(m5 "$(live "$n")") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h; the database backup stays: $DBBAK; the table order_carry and the column s454_line_edit.reason stay, unread"
  rm -f "$OFFSW"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab diff xargs; do
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
for n in $EFIN; do [ -f "$(live "$n")" ] || { say "!! [1/12] $(live "$n") is not there - nothing installed"; exit 1; }; done
DM5="$(m5 "$BRIEFS/DUTY_MAP.json")"
[ "$DM5" = "$DUTY_V18" ] || [ "$DM5" = "$(m5 "$KDIR/DUTY_MAP.json")" ] || { say "!! [1/12] the clone's DUTY_MAP.json is $DM5: neither v18 nor this kit's v19 - nothing installed"; exit 1; }
ALL_TO=1; for n in $EFIN $NEWF; do [ "$(m5 "$(live "$n")")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the seven files are the kit's. Nothing written. healthz $(health "$FIN_PORT" /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, DUTY_MAP v18 or v19, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi
stop_unlocked() { say "$1"; [ "${DRY:-0}" = 1 ] || release_lock; exit "${2:-1}"; }

for n in $EFIN; do C="$(m5 "$(live "$n")")"; [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/12] $(live "$n") is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; done
[ -e "$FIN/order_track.py" ] && stop_unlocked "!! [2/12] $FIN/order_track.py already exists (not this kit's) - STOP, nothing installed"
say "[2/12] live pins exact: $(for n in $EFIN; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)order_track.py absent (new)"
say "       the read-only files' live md5s (the brief, section 1):"
for f in "${!READ[@]}"; do C="$(m5 "$f")"; say "         $f $C"; [ "$C" = "${READ[$f]}" ] || stop_unlocked "!! [2/12] $f is $C, not ${READ[$f]} - this kit was built reading it: STOP, nothing installed"; done
for f in "${!PRINT[@]}"; do say "         $f $(m5 "$f") (printed; at the build ${PRINT[$f]:0:8})"; done
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

mkdir -p "$SCR/built" "$SCR/factsfin" || stop_unlocked "!! cannot make $SCR - nothing installed"
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s619.py walk_s619.py order_track.py || stop_unlocked "!! [3/12] compile failed on $py - nothing installed"
done
"$APY" -B make_s619.py --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { mask < "$SCR/make.txt"; stop_unlocked "!! [4/12] the builder refused a live file - nothing installed"; }
for n in $EFIN $NEWF; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; done
for py in "$APY" "$VPY"; do
  for n in order_sheet.py porders_s454.py darpan_kal.py order_sheet_pdf.py marg_order_pdf.py order_track.py; do
    PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || stop_unlocked "!! [3/12] the built $n does not compile on $py - nothing installed"
  done
done
say "[3/12] the kit's python files and the six built python files compile on $APY and $VPY (darpan_kal.html: its script is checked by the walk's pages)"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each at its TO pin"

# ---- the live facts BEFORE: a backup-API copy of finance.db; the live folder with the built files (order_track reads; no page rendered)
cp -p "$FIN"/*.py "$SCR/factsfin/" 2>/dev/null; cp -p "$SCR/built"/* "$SCR/factsfin/"
facts() { copydb "$DB" "$SCR/facts_$1.db" && ( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s619.py" --facts --label "$1" --fin "$SCR/factsfin" --db "$SCR/facts_$1.db" --adb "$ADB" --shared "$SHD" 2>&1 ) | mask; }
say "[4/12] the live facts BEFORE (a backup-API copy; SELECT and order_track's light half -- the section 4.1 table as it will show):"
FB="$(facts before)"; echo "$FB" | sed 's/^/ /'
echo "$FB" | grep -q "^FACTS OK S619 (before)" || stop_unlocked "!! [4/12] the live facts could not be read - nothing installed"

# ---- the wait: no order message queued, none handed in the last 10 minutes (30 minutes at most, every 2; still busy -> STOP)
busy() { "$APY" -c "import sqlite3,sys,datetime as d; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); t=(d.datetime.now()-d.timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S'); print(c.execute(\"SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND (status='queued' OR replace(COALESCE(handed_at,''),' ','T')>=?)\", (t,)).fetchone()[0])" "$DB" 2>/dev/null || echo 1; }
if [ "${DRY:-0}" = 1 ]; then
  say "       the wait: DRY RUN -- not waited ($(busy) order message(s) queued or handed in the last 10 minutes now)"
else
  W0="$(TZ=Asia/Kolkata date '+%H:%M:%S')"; WAITED=0
  while [ "$(busy)" != 0 ] && [ "$WAITED" -lt 30 ]; do say "       $(TZ=Asia/Kolkata date '+%H:%M:%S IST'): $(busy) order message(s) queued or handed in the last 10 minutes -- waiting 2 minutes"; sleep 120; WAITED=$((WAITED+2)); done
  [ "$(busy)" = 0 ] || stop_unlocked "!! the wait: 30 minutes from $W0 IST and an order message is still queued or was just handed -- STOP; the lock released, nothing installed"
  say "       the wait: from $W0 IST, $WAITED minute(s) -- no order message queued, none handed in the last 10 minutes at $(TZ=Asia/Kolkata date '+%H:%M:%S IST')"
fi

# ---- 5: the scratch sides
copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine_live.db" || stop_unlocked "!! [5/12] no copy of the databases - nothing installed"
mkfin() {
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive" "$d/marg_ingest/lib" "$d/shared" "$d/portal"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -p "$MARG"/lib/*.py "$d/marg_ingest/lib/" 2>/dev/null
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  cp -p "$SHD"/*.py "$d/shared/" 2>/dev/null
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$d/portal/"; done
  cp -p "$POR/tile_grants.json" "$d/portal/" || return 1; cp -rp "$POR/forms" "$d/portal/" 2>/dev/null
  for x in por619 por618 por613 por605 por603; do mkdir -p "$d/$x" && cp -rp "$d/portal/." "$d/$x/"; done
  for x in f619 f613 f605 f603 f598 f618; do cp -p "$SCR/base.db" "$d/$x.db" || return 1; done
  cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/base_a.db" "$d/a619.db"
  cp -p "$SCR/spine_live.db" "$d/finance/spine/spine.db"
}
for side in new old; do rm -rf "$SCR/$side"; mkfin "$side" || stop_unlocked "!! [5/12] no scratch side '$side' - nothing installed"; done
for n in $EFIN $NEWF; do cp -p "$SCR/built/$n" "$SCR/new/finance/$n"; done
say "[5/12] scratch: finance.db, assets.db and the spine by the backup API; the finance folder twice -- NEW (the seven built files) and OLD (as they are);"
say "       marg_ingest's scripts and archived order sheets, /root/shared and a portal copy per walk on each side"

# ---- 6: the walks
w619() { ( cd /tmp && timeout 3600 "$APY" -B "$KDIR/walk_s619.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f619.db" --adb "$SCR/$1/a619.db" --marg "$SCR/$1/marg_ingest" \
          --shared "$SCR/$1/shared" --por "$SCR/$1/por619" --duty-map "$KDIR/DUTY_MAP.json" --dump "$SCR/dump_$1" "${@:2}" 2>&1 ); }
ROUT="$(w619 old --expect-red)"; RRC=$?
WOUT="$(w619 new --old-dump "$SCR/dump_old")"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
[ "$WRC" = 0 ] && echo "$WOUT" | grep -q "^WALK OK S619" || stop_unlocked "!! [6/12] walk_s619 is RED on this box (exit $WRC) - nothing installed"
echo "$ROUT" | mask | grep -E "^  red: |^  NOT RED|^WALK OK negative|^NEGATIVE CONTROL|^WALK RED" | sed 's/^/   /'
[ "$RRC" = 0 ] && echo "$ROUT" | grep -q "^WALK OK negative control S619" || { echo "$ROUT" | mask | tail -40; stop_unlocked "!! [6/12] the negative control did not go red on the old files - nothing installed"; }
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S619: //')"
if [ "${QUICK:-0}" = 1 ] && [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN (QUICK): S619's walk only; NOTHING written"; exit 0; fi
# the earlier walks on the OLD (live) and the NEW side: a NEW red line must be one this kit changes on purpose (brief 4.9), printed both ways
d="$SCR/sp_old605"; mkdir -p "$d"; cp -p "$SPN/spine_read.py" "$d/"; cp -p "$OLD605" "$d/spine_build.py"
[ "$(m5 "$OLD605")" = "$OLD605_MD5" ] || stop_unlocked "!! [6/12] S605's OLD spine builder is not at its md5 - nothing installed"
( cd "$d" && timeout 1200 "$VPY" -B spine_build.py --readings "$SPN/readings" --rules "$SPN/spine_rules.json" --out "$d/spine.db" --finance-db "$SCR/base.db" > "$d/build.txt" 2>&1 )
grep -q "^SPINE BUILT" "$d/build.txt" || stop_unlocked "!! [6/12] S605's OLD builder did not build a scratch spine - nothing installed"
mkdir -p "$SCR/ar618/static" "$SCR/up618"
cp -p "$AR"/*.py "$AR"/*.js "$SCR/ar618/" 2>/dev/null; cp -p "$AR"/static/opencv.js* "$SCR/ar618/static/" 2>/dev/null
"$APY" -c "
import sqlite3,sys,shutil,os
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
for (f,) in c.execute(\"SELECT source_stored FROM bills WHERE lane='pharmacy' AND substr(created_at,1,10)>='2026-10-08' AND source_stored IS NOT NULL\"):
    p=os.path.join(sys.argv[2],f)
    if os.path.exists(p):
        shutil.copy2(p,os.path.join(sys.argv[3],f))" "$SCR/base_a.db" "$UPL" "$SCR/up618" || stop_unlocked "!! [6/12] the scans could not be copied to scratch - nothing installed"
w618() { rm -rf "$SCR/$1/ar618" "$SCR/$1/up618"; cp -rp "$SCR/ar618" "$SCR/$1/ar618"; cp -rp "$SCR/up618" "$SCR/$1/up618"; cp -p "$SCR/base_a.db" "$SCR/$1/a618.db"
         ( cd /tmp && timeout 5400 "$APY" -B "$K618/walk_s618.py" --ar "$SCR/$1/ar618" --fin "$SCR/$1/finance" --shared "$SCR/$1/shared" --adb "$SCR/$1/a618.db" \
           --db "$SCR/$1/f618.db" --uploads "$SCR/$1/up618" --por "$SCR/$1/por618" --duty-map "$K618/DUTY_MAP.json" --labels "$K618/S335_SCAN_VISUAL_AUDIT.json" \
           --kit "$K618" --vpy "$VPY" --dump "$SCR/d618_$1" 2>&1 ); }
w613() { ( cd /tmp && timeout 2400 "$APY" -B "$K613/walk_s613.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f613.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por613" \
          --duty-map "$K605/DUTY_MAP.json" --spine-old605 "$SCR/sp_old605/spine.db" --dump "$SCR/d613_$1" 2>&1 ); }
w605() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s605.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f605.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por605" --duty-map "$K605/DUTY_MAP.json" --dump "$SCR/d605_$1" 2>&1 ); }
w603() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s603.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f603.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por603" --duty-map "$S603KIT/DUTY_MAP.json" --dump "$SCR/d603_$1" 2>&1 ); }
w598() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s598.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f598.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --kit "$S598KIT" --rows-json "$ROWS598" --dump "$SCR/d598_$1" 2>&1 ); }
wlines() { grep -E '^  (ok|FAIL) ' | sed -E 's/   \[.*$//; s/[0-9]+\.[0-9]+s/N.Ns/g; s/[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?/HH:MM/g; s/\(200, [0-9]+ bytes\)/(200, N bytes)/; s/[0-9]{10,}/##########/g'; }
BAD=0
for w in 618 613 605 603 598; do
  for side in old new; do cp -p "$SCR/base_a.db" "$SCR/$side/a.db"; done
  O="$(w$w old)"; ORC=$?; N="$(w$w new)"; NRC=$?
  echo "$O" | wlines > "$SCR/w${w}_old.txt"; echo "$N" | wlines > "$SCR/w${w}_new.txt"
  say "       walk_s$w -- on the OLD (live) files: $(echo "$O" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $ORC); on the NEW files: $(echo "$N" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $NRC)"
  [ -s "$SCR/w${w}_new.txt" ] || stop_unlocked "!! [6/12] walk_s$w printed no check line - nothing installed"
  diff "$SCR/w${w}_old.txt" "$SCR/w${w}_new.txt" | grep -E '^[<>] ' > "$SCR/w${w}_diff.txt"
  if [ -s "$SCR/w${w}_diff.txt" ]; then
    say "         its check lines that differ, both ways (< OLD, > NEW):"; mask < "$SCR/w${w}_diff.txt" | cut -c1-260 | sed 's/^/           /'
    NB="$(grep '^> *FAIL ' "$SCR/w${w}_diff.txt" | grep -v -i -E "$ALLOW" | head -5)"
    if [ -n "$NB" ]; then say "         a NEW red line this kit does not change on purpose:"; echo "$NB" | mask | sed 's/^/           !! /'; BAD=1; fi
  else
    say "         every check line equal OLD vs NEW ($(wc -l < "$SCR/w${w}_new.txt") lines)"
  fi
  grep '^  FAIL ' "$SCR/w${w}_old.txt" | cut -c1-200 | sed 's/^/         red on the OLD (live) side too: /'
done
find "$KDIR" "$K605" "$K613" "$K618" "$S603KIT" "$S598KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
[ "$BAD" = 0 ] || stop_unlocked "!! [6/12] an earlier walk goes red on the NEW files where this kit changes nothing on purpose - nothing installed"
for n in $EFIN; do [ "$(m5 "$(live "$n")")" = "${FROM[$n]}" ] || stop_unlocked "!! [6/12] $(live "$n") changed during the walks - nothing installed"; done
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the live facts, the scratch sides and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 7: backups
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; stop_unlocked "!! [7/12] finance.db backup failed - nothing placed"; }
for n in $EFIN; do
  \cp -p "$(live "$n")" "$(bak "$n")" || stop_unlocked "!! [7/12] backup of $n failed - nothing placed"
  [ "$(m5 "$(bak "$n")")" = "${FROM[$n]}" ] || stop_unlocked "!! [7/12] the backup of $n is not the live file - nothing placed"
done
say "[7/12] backups: $(basename "$DBBAK") ($(stat -c %s "$DBBAK") bytes, the sqlite backup API); $(for n in $EFIN; do printf '%s ' "$(basename "$(bak "$n")")"; done)"

# ---- 8-9: the files in ONE move; the table and the column; one restart
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || stop_unlocked "!! [8/12] could not write $OFFSW - nothing placed"
for n in $EFIN $NEWF; do
  { if [ -f "$(live "$n")" ]; then \cp -p "$(live "$n")" "$(stg "$n")"; else : > "$(stg "$n")"; chmod 644 "$(stg "$n")"; fi; } && cat "$SCR/built/$n" > "$(stg "$n")" && [ "$(m5 "$(stg "$n")")" = "${TO[$n]}" ] \
    || { rm -f "$FIN"/.*.s619 "$OFFSW"; stop_unlocked "!! [8/12] could not stage $n - nothing placed"; }
done
PLACED=1
MV=""; for n in $EFIN $NEWF; do MV="$MV mv -f '$(stg "$n")' '$(live "$n")' &&"; done
eval "${MV% &&}" || restore "placing the files"
for n in $EFIN $NEWF; do [ "$(m5 "$(live "$n")")" = "${TO[$n]}" ] && cmp -s "$(live "$n")" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[8/12] placed by rename in ONE command; md5 read back: $(for n in $EFIN $NEWF; do printf '%s %s . ' "$n" "$(m5 "$(live "$n")" | cut -c1-8)"; done)(= the TO pins, byte-identical to the walked files)"
ENS="$( cd /tmp && "$APY" -B -c "
import sqlite3, sys
sys.path.insert(0, sys.argv[1])
import order_sheet as OS
c = sqlite3.connect(sys.argv[2], timeout=60)
OS.ensure(c)
print('order_carry' if c.execute(\"SELECT 1 FROM sqlite_master WHERE name='order_carry'\").fetchone() else 'NO order_carry',
      'reason' if 'reason' in [r[1] for r in c.execute('PRAGMA table_info(s454_line_edit)')] else 'NO reason',
      sorted(r[0] for r in c.execute(\"SELECT key FROM setting WHERE key IN ('order.deliver_days','order.deliver_skip','order.deliver_window','order.wa_delivery_line','order.track_since')\")))
" "$FIN" "$DB" 2>&1 | tail -1)"
echo "$ENS" | grep -q "^order_carry reason" || restore "the table and the column were not made ($ENS)"
say "        the table and the column (order_sheet.ensure on live, guarded): $ENS"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart clinic-finance || restore "restart clinic-finance"
c1=000; for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health "$FIN_PORT" /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet clinic-finance || restore "clinic-finance is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FIN_PORT" /finance/porders); c3=$(health "$FIN_PORT" /finance/porders/s454/late); c4=$(health "$FIN_PORT" /finance/porders/s454/track); c5=$(health "$FIN_PORT" /finance/darpan/kal/api/day)
for c in "$c2" "$c3" "$c4" "$c5"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): porders $c2 / s454/late $c3 / s454/track $c4 / darpan day $c5";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[9/12] clinic-finance restarted at $T0 (the box's clock) and active - healthz $c1 - /finance/porders $c2, /s454/late $c3, /s454/track $c4, darpan day $c5"
say "        without a login (302 = the login gate, expected) - journal clean; nothing else restarted"

# ---- 10: the first carry pass on live (order_track.carry_pass, keyed by line -- the step cron_pass runs); the facts AFTER; the duty map's SQL
CP="$( cd /tmp && "$APY" -B -c "
import sqlite3, sys
sys.path.insert(0, sys.argv[1])
import order_sheet as OS, order_track as OT
c = sqlite3.connect(sys.argv[2], timeout=60); c.row_factory = sqlite3.Row
print('carry_pass', OT.carry_pass(c, OS.now(), who='S619 install'))
" "$FIN" "$DB" 2>&1 | tail -1)"
say "[10/12] the first carry pass on live: $CP"
echo "$CP" | grep -q "^carry_pass {" || restore "the first carry pass did not run ($CP)"
say "        the live facts AFTER (a backup-API copy):"
FA="$(facts after)"; echo "$FA" | sed 's/^/ /'
echo "$FA" | grep -q "^FACTS OK S619 (after)" || restore "the live facts after placing could not be read"
for k in reception.order_arrival reception.medicine_orders reception.bill_scan shavez.order_followup; do
  say "        DUTY_MAP $k due_sql on live (read only): $(sqlro "$DB" "$("$APY" -c "import json,sys; print([d for d in json.load(open(sys.argv[1]))['duties'] if d['id']==sys.argv[2]][0]['due_sql'])" "$KDIR/DUTY_MAP.json" "$k")" | tr -s ' ')"
done
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(kits5)" = "$KITS0" ] || restore "a published S5*/S6* kit folder moved"
[ "$(health "$FIN_PORT" /finance/healthz)" = 200 ] || restore "healthz at the end"
PLACED=0
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, portal.py, tile_grants.json, the crontab, the published kit folders); healthz 200; $OFFSW removed"

# ---- 11: md5 read back
say "[11/12] md5 read back:"
for n in $EFIN $NEWF; do md5sum "$(live "$n")"; done
say "[12/12] $KIT: DONE. The build lock stays held by $KIT until the report is written (release: rm -f $LOCK/owner; rmdir $LOCK)."
say "undo (the files): $(for n in $EFIN; do printf '\\cp -p %s %s && ' "$(bak "$n")" "$(live "$n")"; done)mv $FIN/order_track.py $FIN/order_track.py.undone && $SYSTEMCTL restart clinic-finance"
exit 0
