#!/bin/bash
# =============================================================================
#  install_S613_S605_FOLLOWUP.sh · kit S613 (22-Oct-2026) · brief claude_code_briefs/S613_S605_FOLLOWUP.md (v2, Sanjeevni session 335)
#  F-951 (the readers' half: a split size figured by its share up to the split day and its own key after; bills matched by size across it),
#  F-959 (the old Purchase orders page orders nothing from Yuvika), F-962 (the call row counts today's orders still awaited),
#  F-960 (the wait from the hand-out; a late 'could not send' brings an unconfirmed order back; once per 'no'), F-957 (S604's walk lays its days).
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S613_S605_FOLLOWUP), 08:02-23:49 IST only:
#    rm -rf /tmp/s613kit && cp -rp <kit> /tmp/s613kit && bash /tmp/s613kit/install_S613_S605_FOLLOWUP.sh
#  (DRY=1 before bash: every gate, the live facts, the scratch sides and every walk; nothing written, no lock, no wait.)
#
#   /root/finance/stock_figure.py   51e1fc63 -> TO  split_of / split_members / split_share / split_moves; shelf, marg, spine_move, carried read them
#   /root/finance/order_sheet.py    17fa1fdb -> TO  withdraw_late from handed_at (guarded); on_message_done's late no; _s613_phone_said_no; owner line
#   /root/finance/porders_s454.py   7ca91d4f -> TO  the call row's count (home() only); _done_today's numbers through OS.book_card
#   /root/finance/porders.py        e5a5c4d4 -> TO  api_send refuses (409 ortho_via_order_page), its body retired
#   /root/finance/porders.html      7a6799ae -> TO  the Yuvika button, send(), dq, ps, QTY, PICK and the send / sizes words removed
#  finance.db: no DDL, no DELETE, no hand edit, no setting. spine.db: not edited, not rebuilt. DUTY_MAP: no change.
#  ORDER: gates -> the lock -> the five FROM pins, the read-only md5s, the kit folders' files -> the spine green and fresh -> the live facts
#  BEFORE (SELECTs and a read-only Ctx: never a page) -> the wait (30 min at most, every 2; still active -> STOP) -> build from the live bytes
#  -> compile (both pythons) -> scratch: S605's OLD builder spine, the finance folder twice (OLD, NEW) -> walk_s613 OLD (red) then NEW ->
#  walk_s604_v2 NEW (green) and on S604's OLD purchase_app (red) -> S605's walk_s605 / walk_s603 / walk_s598 on OLD and NEW (only this kit's
#  lines differ) -> DRY stops -> backups -> DOCTOR_AUTO_OFF -> the files staged and renamed in ONE command -> md5 read back -> ONE restart of
#  clinic-finance -> healthz 200, the pages 302 -> journal clean -> the live facts AFTER, detect_supplies' writes on live since placing ->
#  nothing else moved -> DOCTOR_AUTO_OFF removed -> the witness once (read only; writes spine/stock_figure_witness_<Day>.txt).
#  Red after placing: the files back from their .bak_S613_<from8>, one restart, healthz. The lock stays held until the report is written
#  (released with rm -f .../owner; rmdir ...). Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S613_S605_FOLLOWUP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
DB="${DB:-$FIN/finance.db}"
REPO="${REPO:-/root/deploy/repo}"
BRIEFS="$REPO/claude_code_briefs"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
K605="$REPO/deploy_kits/S605_ORDER_FIXES"
K604="$REPO/deploy_kits/S604_PAY_SHEET_FIXES"
S603KIT="$REPO/deploy_kits/S603_AMIR_CALENDAR_SAFE"
S598KIT="$REPO/deploy_kits/S598_ARRIVALS_BY_LINE"
ROWS598="$FIN/purchase_order_line.bak_S598_20261019_095314.json"
ROWS598_MD5=a0d31a256afd3cdabdcdf1a4b3a54166
SUMS605_MD5_8=018a68ad
OLD605="$SPN/spine_build.py.bak_S605_e3d3ed85"; OLD605_MD5=e3d3ed85973eab2df0326dc9621e230e
OLD604="$FIN/purchase_app.py.bak_S604_60f2d846"; OLD604_MD5=60f2d846155659c4eddc33e4a0d42b39
DUTY_V17=ef42b15568f681b1942abcc6639bec57
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDITED="stock_figure.py order_sheet.py porders_s454.py porders.py porders.html"
declare -A FROM TO READ
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s613_inst_$STAMP"
PLACED=0
DBBAK="$FIN/finance.db.bak_S613_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S613_${FROM[$1]:0:8}"; }
stg() { echo "$FIN/.$1.s613"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" "$K605" "$K604" "$S603KIT" "$S598KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
sqlro() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); [print('   ', *[str(x) for x in r]) for r in c.execute(sys.argv[2]).fetchall()]" "$1" "$2" 2>/dev/null | mask; }
release_lock() { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back from their .bak_S613_* in one command"
  for n in $EDITED; do \cp -p "$(bak "$n")" "$FIN/$n" || say "   !! could not put back $n"; done
  rm -f "$FIN"/.*.s613
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h; the database backup stays: $DBBAK"
  rm -f "$OFFSW"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab diff; do
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
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/12] $FIN/$n is not there - nothing installed"; exit 1; }; done
# the kit folders left byte-identical (F-512): S605 whole by its SUMS (and SUMS itself at the brief's 018a68ad); S604's files by its SUMS but
# KIT_MANIFEST.txt (F-958: line endings in a git clone); S603's DUTY_MAP.json and S598's two files that S605's walks read
( cd "$K605" && md5sum -c SUMS.md5 >/dev/null 2>&1 ) && [ "$(m5 "$K605/SUMS.md5" | cut -c1-8)" = "$SUMS605_MD5_8" ] || { say "!! [1/12] $K605 fails its SUMS (or SUMS is not 018a68ad) - nothing installed"; exit 1; }
( cd "$K604" && grep -v 'KIT_MANIFEST.txt' SUMS.md5 | md5sum -c - >/dev/null 2>&1 ) || { say "!! [1/12] $K604 fails its SUMS (KIT_MANIFEST.txt apart) - nothing installed"; exit 1; }
for kf in "$S603KIT:DUTY_MAP.json" "$S598KIT:rejudge_s598.py" "$S598KIT:undo_s598.py"; do
  k="${kf%%:*}"; f="${kf#*:}"
  ( cd "$k" && grep -E "  $f\$" SUMS.md5 | md5sum -c - >/dev/null 2>&1 ) || { say "!! [1/12] $k/$f is missing or fails its kit's SUMS - nothing installed"; exit 1; }
done
[ "$(m5 "$ROWS598")" = "$ROWS598_MD5" ] || { say "!! [1/12] the S598 install's rows JSON is not at its pin - nothing installed"; exit 1; }
[ "$(m5 "$OLD605")" = "$OLD605_MD5" ] || { say "!! [1/12] S605's OLD spine builder ($OLD605) is not at its md5 - nothing installed"; exit 1; }
[ "$(m5 "$OLD604")" = "$OLD604_MD5" ] || { say "!! [1/12] S604's OLD purchase_app ($OLD604) is not at its md5 - nothing installed"; exit 1; }
DM5="$(m5 "$BRIEFS/DUTY_MAP.json")"
[ "$DM5" = "$DUTY_V17" ] || { say "!! [1/12] the clone's DUTY_MAP.json is $DM5, not v17 ($DUTY_V17) -- this kit was built reading v17: nothing installed"; exit 1; }
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the five files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, the S605 / S604 / S603 / S598 kit files, S598's rows, S605's and S604's OLD files, DUTY_MAP v17, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi
stop_unlocked() { say "$1"; [ "${DRY:-0}" = 1 ] || release_lock; exit "${2:-1}"; }

for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/12] $FIN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; done
say "[2/12] live pins exact: $(for n in $EDITED; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)"
say "       the read-only files' live md5s (the brief, section 1):"
for n in "${!READ[@]}"; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || stop_unlocked "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"
done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] && [ -d "$SPN/readings" ] && [ -f "$POR/tile_grants.json" ] || stop_unlocked "!! [2/12] a database, the spine or the portal is missing - nothing installed"
CRONN="$(crontab -l 2>/dev/null | wc -l | awk '{print $1}')"
[ "$CRONN" = 84 ] || stop_unlocked "!! [2/12] the crontab is not as the brief read it (84 lines; now $CRONN) - STOP, nothing installed"
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
[ "$SP_OK" = True ] && [ "$SP_GATE" = "13/13" ] && [ "$SP_AGE" -le 30 ] \
  || stop_unlocked "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - nothing installed" 4
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
for n in "${!READ[@]}"; do NOTT+=("$FIN/$n"); done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "       the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); the crontab $CRONN lines; the clone's DUTY_MAP.json v17 (${DUTY_V17:0:8}): no change by this kit"

mkdir -p "$SCR/built" "$SCR/code_live" || stop_unlocked "!! cannot make $SCR - nothing installed"
export PYTHONDONTWRITEBYTECODE=1
codecopy() { local d="$1"; mkdir -p "$d/spine"; cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$d/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/spine/" 2>/dev/null; }
facts() {   # $1 label, $2 code folder: read only (finance.db by mode=ro, the spine by mode=ro, a read-only Ctx) -- never a page
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s613.py" --facts --label "$1" --fin "$2" --db "$DB" --spine "$SPN/spine.db" 2>&1 ) | mask
}
codecopy "$SCR/code_live"
say "[2/12] the live facts BEFORE (SELECTs and a read-only Ctx over the live database and spine; no page is rendered):"
FB="$(facts before "$SCR/code_live")"; echo "$FB" | sed 's/^/ /'
echo "$FB" | grep -q "^FACTS OK S613 (before)" || stop_unlocked "!! [2/12] the live facts could not be read - nothing installed"
say "         today's purchase_audit rows of the order messages (action, at, ref):"
sqlro "$DB" "SELECT action, substr(at,12,8), ref FROM purchase_audit WHERE action LIKE 's454_whatsapp%' AND substr(at,1,10)=date('now','localtime') ORDER BY id"

# ---- the wait: no order message queued, or handed in the last 10 minutes (30 minutes at most, every 2; still active -> STOP)
busy() { "$APY" -c "import sqlite3,sys,datetime as d; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); t=(d.datetime.now()-d.timedelta(minutes=10)).replace(microsecond=0).isoformat(); print(c.execute(\"SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND (status='queued' OR replace(COALESCE(handed_at,''),' ','T')>=?)\", (t,)).fetchone()[0])" "$DB" 2>/dev/null || echo 1; }
if [ "${DRY:-0}" = 1 ]; then
  say "       the wait: DRY RUN -- not waited ($(busy) order message(s) queued or handed in the last 10 minutes now)"
else
  W0="$(TZ=Asia/Kolkata date '+%H:%M:%S')"; WAITED=0
  while [ "$(busy)" != 0 ] && [ "$WAITED" -lt 30 ]; do say "       $(TZ=Asia/Kolkata date '+%H:%M:%S IST'): $(busy) order message(s) queued or handed in the last 10 minutes -- waiting 2 minutes"; sleep 120; WAITED=$((WAITED+2)); done
  [ "$(busy)" = 0 ] || stop_unlocked "!! the wait: 30 minutes from $W0 IST and still $(busy) order message(s) active -- STOP (the brief: never proceed); the lock released, nothing installed"
  say "       the wait: from $W0 IST, $WAITED minute(s) -- no order message queued or handed in the last 10 minutes at $(TZ=Asia/Kolkata date '+%H:%M:%S IST')"
fi

for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s613.py walk_s613.py walk_s604_v2.py || stop_unlocked "!! [3/12] compile failed on $py - nothing installed"
done
"$APY" -B make_s613.py --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { mask < "$SCR/make.txt"; stop_unlocked "!! [4/12] the builder refused a live file - nothing installed"; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do case "$n" in *.py) PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || stop_unlocked "!! [3/12] the built $n does not compile on $py - nothing installed";; esac; done
done
say "[3/12] the kit's python files and the four built python files compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each at its TO pin"

# ---- 5: the scratch sides
copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine_live.db" || stop_unlocked "!! [5/12] no copy of the databases - nothing installed"
d="$SCR/sp_old605"; mkdir -p "$d"; cp -p "$SPN/spine_read.py" "$d/"; cp -p "$OLD605" "$d/spine_build.py"
( cd "$d" && timeout 1200 "$VPY" -B spine_build.py --readings "$SPN/readings" --rules "$SPN/spine_rules.json" --out "$d/spine.db" --finance-db "$SCR/base.db" > "$d/build.txt" 2>&1 )
SPO=$?
grep -q "^SPINE BUILT" "$d/build.txt" && [ "$SPO" = 0 ] || stop_unlocked "!! [5/12] S605's OLD builder did not build a scratch spine (exit $SPO) - nothing installed"
mkside() {
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive" "$d/marg_ingest/lib" "$d/portal"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -p "$MARG"/lib/*.py "$d/marg_ingest/lib/" 2>/dev/null
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$d/portal/"; done
  cp -p "$POR/tile_grants.json" "$d/portal/" || return 1; cp -rp "$POR/forms" "$d/portal/" 2>/dev/null
  for x in por604 por605 por603; do mkdir -p "$d/$x" && cp -rp "$d/portal/." "$d/$x/"; done
  for x in f f604 f605 f603 f598; do cp -p "$SCR/base.db" "$d/$x.db" || return 1; done
  cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/spine_live.db" "$d/finance/spine/spine.db"
}
for side in new old o604; do rm -rf "$SCR/$side"; mkside "$side" || stop_unlocked "!! [5/12] no scratch side '$side' - nothing installed"; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/$n"; done
cp -p "$OLD604" "$SCR/o604/finance/purchase_app.py"
say "[5/12] scratch: S605's OLD builder spine (built from the live readings); the finance folder three times -- NEW (the five built files), OLD (as it"
say "       is), and OLD with S604's own OLD purchase_app (F-957); a portal copy per walk; finance.db, assets.db and the spine by the backup API"

# ---- 6: the walks
w613() { ( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s613.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/portal" \
          --duty-map "$BRIEFS/DUTY_MAP.json" --spine-old605 "$SCR/sp_old605/spine.db" --dump "$SCR/dump_$1" "${@:2}" 2>&1 ); }
ROUT="$(w613 old --expect-red)"; RRC=$?
WOUT="$(w613 new --old-dump "$SCR/dump_old")"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
[ "$WRC" = 0 ] && echo "$WOUT" | grep -q "^WALK OK S613" || stop_unlocked "!! [6/12] walk_s613 is RED on this box (exit $WRC) - nothing installed"
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  red: |^  NOT RED|^WALK OK negative|^NEGATIVE CONTROL|^WALK RED" | sed 's/^/   /'
[ "$RRC" = 0 ] && echo "$ROUT" | grep -q "^WALK OK negative control S613" || { echo "$ROUT" | mask | tail -30; stop_unlocked "!! [6/12] the negative control did not go red on the old files - nothing installed"; }
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S613: //')"
w604() { ( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s604_v2.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f604.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por604" --dump "$SCR/d604_$1" "${@:2}" 2>&1 ); }
N604="$(w604 new)"; N604RC=$?; O604="$(w604 o604 --expect-red)"; O604RC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "       F-957 -- walk_s604_v2 on the NEW files: $(echo "$N604" | grep -E '^WALK (OK|RED)' | tail -1 | mask) (exit $N604RC)"
echo "$N604" | grep -E '^  FAIL |not re-walked' | mask | cut -c1-220 | sed 's/^/           /'
say "       ... on S604's own OLD purchase_app (60f2d846): $(echo "$O604" | grep -E '^WALK (OK|RED)' | tail -1 | mask) (exit $O604RC)"
echo "$O604" | grep -E '^  NOT RED' | mask | cut -c1-220 | sed 's/^/           /'
[ "$N604RC" = 0 ] && echo "$N604" | grep -q "^WALK OK S604v2" && [ "$O604RC" = 0 ] && echo "$O604" | grep -q "^WALK OK negative control S604v2" \
  || stop_unlocked "!! [6/12] walk_s604_v2 is not green on NEW, or its controls not red on S604's OLD purchase_app - nothing installed"
# S605's three walks on the OLD (live) and the NEW side: only the lines this kit changes on purpose may differ
w605() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s605.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f605.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por605" --duty-map "$K605/DUTY_MAP.json" --dump "$SCR/d605_$1" 2>&1 ); }
w603() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s603.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f603.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por603" --duty-map "$S603KIT/DUTY_MAP.json" --dump "$SCR/d603_$1" 2>&1 ); }
w598() { ( cd /tmp && timeout 2400 "$APY" -B "$K605/walk_s598.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f598.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --kit "$S598KIT" --rows-json "$ROWS598" --dump "$SCR/d598_$1" 2>&1 ); }
wlines() { grep -E '^  (ok|FAIL) ' | sed -E 's/   \[.*$//; s/[0-9]+\.[0-9]+s/N.Ns/g; s/[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?/HH:MM/g; s/\(200, [0-9]+ bytes\)/(200, N bytes)/; s/[0-9]{10,}/##########/g'; }
ALLOW605='^  (ok|FAIL) +C: \(2\) \.\.\. and a send-all never queues again a message the phone was handed \(call instead\)$|^  (ok|FAIL) +C: \(4\) nothing left to order -> .Aaj ke order — call karo. with the Ho chuke count'
ALLOW603='^  (ok|FAIL) +stock_figure\.py untouched \(md5 51e1fc63\)$'
ALLOW598="^  (ok|FAIL) +C: after the re-judge the owner's arrival lines carry the clause for XXL"
for w in 605 603 598; do
  O="$(w$w old)"; ORC=$?; N="$(w$w new)"; NRC=$?
  echo "$O" | wlines > "$SCR/w${w}_old.txt"; echo "$N" | wlines > "$SCR/w${w}_new.txt"
  eval "AL=\$ALLOW$w"
  say "       walk_s$w (S605's folder) -- on the OLD (live) files: $(echo "$O" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $ORC); on the NEW files: $(echo "$N" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $NRC)"
  [ -s "$SCR/w${w}_new.txt" ] || stop_unlocked "!! [6/12] walk_s$w printed no check line - nothing installed"
  diff "$SCR/w${w}_old.txt" "$SCR/w${w}_new.txt" | grep -E '^[<>] ' > "$SCR/w${w}_diff.txt"
  if [ -s "$SCR/w${w}_diff.txt" ]; then
    say "         its check lines that differ, both ways (< the OLD files, > the NEW):"; mask < "$SCR/w${w}_diff.txt" | cut -c1-230 | sed 's/^/           /'
    if sed -E 's/^[<>] //' "$SCR/w${w}_diff.txt" | grep -vE "$AL" | grep -q .; then stop_unlocked "!! [6/12] walk_s$w differs OLD vs NEW beyond this kit's own lines - nothing installed"; fi
    say "         = only this kit's own lines (brief 4.6)"
  else
    say "         every check line equal OLD vs NEW"
  fi
  grep '^  FAIL ' "$SCR/w${w}_old.txt" | grep -vE "$AL" | cut -c1-200 | sed 's/^/         red on both sides (the live day, not this kit): /'
done
find "$KDIR" "$K605" "$K604" "$S603KIT" "$S598KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || stop_unlocked "!! [6/12] $FIN/$n changed during the walks - nothing installed"; done
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the live facts, the scratch sides and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 7: backups
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; stop_unlocked "!! [7/12] database backup failed - nothing placed"; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak "$n")" || stop_unlocked "!! [7/12] backup of $n failed - nothing placed"
  [ "$(m5 "$(bak "$n")")" = "${FROM[$n]}" ] || stop_unlocked "!! [7/12] the backup of $n is not the live file - nothing placed"
done
say "[7/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak "$n")")"; done)"

# ---- 8-9: the files in ONE move, one restart
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || stop_unlocked "!! [8/12] could not write $OFFSW - nothing placed"
for n in $EDITED; do
  { \cp -p "$FIN/$n" "$(stg "$n")" && cat "$SCR/built/$n" > "$(stg "$n")" && [ "$(m5 "$(stg "$n")")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s613 "$OFFSW"; stop_unlocked "!! [8/12] could not stage $n - nothing placed"; }
done
PLACED=1
MV=""; for n in $EDITED; do MV="$MV mv -f '$(stg "$n")' '$FIN/$n' &&"; done
eval "${MV% &&}" || restore "placing the files"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[8/12] placed by rename in ONE command; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the TO pins, byte-identical to the walked files)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/porders); c3=$(health /finance/porders/s454/order); c4=$(health "/finance/porders?old=1"); c5=$(health /finance/amir); c6=$(health /finance/darpan/kal)
for c in "$c2" "$c3" "$c4" "$c5" "$c6"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): porders $c2 / s454/order $c3 / ?old=1 $c4 / amir $c5 / darpan/kal $c6";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[9/12] $SVC restarted at $T0 (the box's clock; nothing else restarted) and active - healthz $c1 - /finance/porders $c2, /s454/order $c3, ?old=1 $c4, /amir $c5, /darpan/kal $c6 without a login (302 = the login gate, expected) - journal clean"

# ---- 10: the state AFTER; detect_supplies' writes on live since placing; nothing else moved
rm -rf "$SCR/code_after"; codecopy "$SCR/code_after"
say "[10/12] the live facts AFTER placing (the placed files; read only):"
FA="$(facts after "$SCR/code_after")"; echo "$FA" | sed 's/^/ /'
echo "$FA" | grep -q "^FACTS OK S613 (after)" || restore "the live facts after placing could not be read"
echo "$FA" | grep -q "stock_figure 1.4 (S613_S605_FOLLOWUP)" || restore "the live facts after placing do not read the NEW stock_figure"
say "         detect_supplies' writes on live since placing (purchase_audit line_detected; the lines' detected_at):"
sqlro "$DB" "SELECT 'audit', at, ref, detail FROM purchase_audit WHERE action='line_detected' AND replace(at,'T',' ')>='$T0' ORDER BY id"
sqlro "$DB" "SELECT 'line', id, item, billed_bill_no, detected_at FROM purchase_order_line WHERE replace(COALESCE(detected_at,''),'T',' ')>='$T0' ORDER BY id"
say "         (nothing listed = no write)"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
PLACED=0
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, portal.py, tile_grants.json, the crontab); healthz 200; $OFFSW removed"

# ---- 11: md5 read back; the witness once (read only)
say "[11/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
WD="$(TZ=Asia/Kolkata date +%a)"
WERR="$( { cd "$FIN" && "$VPY" -B stock_figure.py witness >/dev/null; } 2>&1 )"; WRC=$?
say "        the witness, once, read only (exit $WRC; stderr: ${WERR:-empty}): $(ls -l "$SPN/stock_figure_witness_$WD.txt" 2>/dev/null | awk '{print $6, $7, $8, $9}')"
find "$FIN" -maxdepth 1 -newer "$SCR/make.txt" -name '__pycache__' 2>/dev/null | head -1 | sed 's/^/        !! a __pycache__ appeared: /'
say "[12/12] $KIT: DONE. The build lock stays held by $KIT until the report is written (release: rm -f $LOCK/owner; rmdir $LOCK)."
say "undo (the files): $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak "$n")" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
