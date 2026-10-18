#!/bin/bash
# =============================================================================
#  install_S577_STOCK_ON_SPINE.sh · kit S577 (18-Oct-2026) · brief claude_code_briefs/S577_STOCK_ON_SPINE.md (v4) · rung 4b of the spine plan
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S577_STOCK_ON_SPINE), 08:00-23:59 IST only:
#    rm -rf /tmp/s577kit && cp -rp <kit> /tmp/s577kit && bash /tmp/s577kit/install_S577_STOCK_ON_SPINE.sh
#  (DRY=1 before bash: every gate, the scratch spines and both walks, nothing written, no lock.)
#
#  ONE place works out stock (stock_figure.py, NEW): Marg's figure and the shelf figure, each on the closing it stands on, by printed name
#  over the spine's own closing captures (sp_close_name, NEW in the spine). Five checks read it: the voucher guard (now with the past-the-shelf
#  half of D715 a), Darpan's spot counts and traces, the shelf-gap flags (s577_shelf_gap, NEW), 'bill entry baaki', the owner's stock-now and
#  drift pages. The Loss desk only reads (sales_test gone, F-841). A renamed item is one item (F-874, F-873). A closing's time is its capture's.
#   /root/finance/spine/spine_build.py    5d8b1f94 -> TO   sp_close_name: every accepted full capture by printed name (the gate unchanged)
#   /root/finance/spine/selftest_spine.py fc63d2c6 -> TO   one more check
#   /root/finance/stock_figure.py         absent   -> NEW  the one stock function
#   /root/finance/stock_app.py            050587df -> TO   the guard (both halves), the stage helpers as wrappers, api_now / api_drift
#   /root/finance/shelf_figure.py         183c70fa -> TO   figures from stock_figure; s577_shelf_gap; latest_snapshot and the stock_feed lookups retired
#   /root/finance/stock_watch.py          0e6a42c4 -> TO   points judged by basis (shelf | marg | approx); key_of; settle on the stored basis
#   /root/finance/loss_piles.py           81ae481e -> TO   the desk only reads; the stamp's spine part = the spine's inputs; one setting (default read)
#  Read only, must not move: item_alias, stockmatch, amir_day, order_rules, qty_words, spine_read, purchase_app, order_sheet, porders_s454,
#  porders, darpan_kal, finance_app, portal.py, tile_grants.json, the crontab (the installer proves none moved). No DUTY_MAP change.
#  ORDER: gates (window, lock, SUMS, KIT_ID, PINS, the spine green and fresh, the 18-10 desk rows) -> pins (ALREADY first) -> build from the
#  live bytes -> compile (both pythons) -> scratch: the finance folder twice, the databases, the readings; the spine built by the NEW and the
#  OLD builder (same sp_close, gate 13/13); selftest; the walk on the OLD files (every control red) then on the NEW files (green) -> DRY stops
#  -> the install-day state on the OLD and the NEW files (a flip or a moved A.pending = STOP) -> backups -> THE SPINE FIRST (two files placed,
#  the live build by the cron command with flock -w 300, sp_close_name filled, gate 13/13, sp_close = the old builder's on the same readings)
#  -> DOCTOR_AUTO_OFF -> the five files staged and renamed in ONE command -> ONE restart of clinic-finance -> healthz 200, the pages 302 ->
#  journal clean -> the state AFTER (no flip) -> nothing else moved -> md5 read-back -> the first witness file -> DOCTOR_AUTO_OFF removed.
#  Red after step 6: the seven files put back in one command, one restart, healthz; sp_close_name / s577_shelf_gap / stock_point.basis stay
#  (additive, read by nothing old). The build lock stays held by S577 until the report is written.
# =============================================================================
set -u
KIT="S577_STOCK_ON_SPINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
REPO="${REPO:-/root/deploy/repo}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
EDITED="stock_app.py shelf_figure.py stock_watch.py loss_piles.py"          # placed in the ONE move, with the new file
SPINEF="spine_build.py selftest_spine.py"                                  # placed first
NEWF="stock_figure.py"
declare -A FROM TO READ
FROM[stock_app.py]=050587dfb5951da65f95937615ddf144
FROM[shelf_figure.py]=183c70fabb64ed1e5a43c645a225c560
FROM[stock_watch.py]=0e6a42c4c7ae51eb8f8a0869fce2d101
FROM[loss_piles.py]=81ae481e4480a12fead3016515037214
FROM[spine_build.py]=5d8b1f94d80189c16b2ee5b1e093429c
FROM[selftest_spine.py]=fc63d2c683a1970c58f60502302187a9
READ[item_alias.py]=111a8e4877035e5a02665dd586e01b06
READ[stockmatch.py]=10e30d28053aca3090e193502b67b1e0
READ[amir_day.py]=73882a8391fde24f31e07b0191c5bd89
READ[order_rules.py]=79f21c1ee1f763b1ac06b370e3d77b79
READ[qty_words.py]=706db7ccfa7489fb8d296f663590f107
READ[purchase_app.py]=98f7d9f05bc06ef6be80181dd9be4c8c
READ[order_sheet.py]=f00f0163bdd66a074c5af261c9b80a49
READ[porders_s454.py]=8307976393e6ea161f8d3a94bcb0692c
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s577_inst_$STAMP"
PLACED=0; SPINE_PLACED=0
DBBAK="$FIN/finance.db.bak_S577_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S577_${FROM[$1]:0:8}"; }
sbak() { echo "$SPN/$1.bak_S577_${FROM[$1]:0:8}"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
closehash() { "$APY" -c "import sqlite3,hashlib,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); r=c.execute('SELECT as_on,k20,units FROM sp_close ORDER BY as_on,k20').fetchall(); print(hashlib.md5(repr(r).encode()).hexdigest()[:12], len(r))" "$1"; }
restore_spine() {
  say "!! RED while placing the spine ($1) - putting the two spine files back"
  for n in $SPINEF; do [ -f "$(sbak $n)" ] && \cp -p "$(sbak $n)" "$SPN/$n"; done
  for n in $SPINEF; do say "   $SPN/$n $(m5 "$SPN/$n") (expected ${FROM[$n]})"; done
  say "   the live spine.db keeps the new table if the build swapped it (additive; nothing old reads it)"
  exit 1
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the seven files back in one command"
  \cp -p "$(bak stock_app.py)" "$FIN/stock_app.py" && \cp -p "$(bak shelf_figure.py)" "$FIN/shelf_figure.py" && \cp -p "$(bak stock_watch.py)" "$FIN/stock_watch.py" && \cp -p "$(bak loss_piles.py)" "$FIN/loss_piles.py" && rm -f "$FIN/$NEWF" && \cp -p "$(sbak spine_build.py)" "$SPN/spine_build.py" && \cp -p "$(sbak selftest_spine.py)" "$SPN/selftest_spine.py"
  rm -f "$FIN"/.*.s577
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  for n in $SPINEF; do say "   $SPN/$n $(m5 "$SPN/$n") (expected ${FROM[$n]})"; done
  say "   $FIN/$NEWF $([ -f "$FIN/$NEWF" ] && echo STILL THERE || echo removed)"
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK; sp_close_name, s577_shelf_gap and stock_point.basis stay (additive; nothing old reads them)"
  rm -f "$OFFSW"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; if [ "$SPINE_PLACED" = 1 ]; then restore_spine "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab flock; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"
[ "$HH" -ge 8 ] || { say "!! [1/14] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:00-23:59 IST (the spine builds */10 8-23) - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/14] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/14] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/14] PINS.sh missing - nothing installed"; exit 1; }
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/14] $FIN/$n is not there - nothing installed"; exit 1; }; done
for n in $SPINEF; do [ -f "$SPN/$n" ] || { say "!! [1/14] $SPN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
for n in $SPINEF; do [ "$(m5 "$SPN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
[ "$(m5 "$FIN/$NEWF")" = "${TO[$NEWF]}" ] || ALL_TO=0
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the seven files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/14] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, the window); no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/14] kit gates green (SUMS, KIT_ID, PINS, the window); the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/14] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/14] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi

for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/14] $FIN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; exit 1; }; done
for n in $SPINEF; do C="$(m5 "$SPN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/14] $SPN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; exit 1; }; done
[ -e "$FIN/$NEWF" ] && { say "!! [2/14] $FIN/$NEWF exists already ($(m5 "$FIN/$NEWF")) - the brief pinned it absent: STOP, nothing installed"; exit 1; }
for n in "${!READ[@]}"; do C="$(m5 "$FIN/$n")"; [ "$C" = "${READ[$n]}" ] || { say "!! [2/14] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }; done
[ "$(m5 "$SPN/spine_read.py")" = "712a1e4ef827f6be4e8b23415c3ceb62" ] || { say "!! [2/14] spine_read.py moved - STOP, nothing installed"; exit 1; }
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] && [ -f "$DMAP" ] && [ -d "$SPN/readings" ] && [ -f "$SPN/spine.db" ] || { say "!! [2/14] a database, the portal, the duty map, the readings or the spine is missing - nothing installed"; exit 1; }
# charter 1b: the spine passed and fresh (under 30 minutes); the 18-10 desk rows (3.3 E)
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/14] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - the kit depends on it; nothing installed (charter 1b)"; exit 4; }
SYSROWS="$("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print(c.execute(\"SELECT (SELECT COUNT(*) FROM stock_shelf_fix WHERE by_user='system' AND at>='2026-10-18')+(SELECT COUNT(*) FROM stock_sales_test WHERE at>='2026-10-18')+(SELECT COUNT(*) FROM stock_diff_lane WHERE by_user='system' AND at>='2026-10-18')\").fetchone()[0])" "$DB" 2>/dev/null || echo 999)"
[ "$SYSROWS" = 0 ] || { say "!! [2/14] $SYSROWS stock_shelf_fix / stock_sales_test / stock_diff_lane row(s) written by the system on or after 2026-10-18 (the desk opened 09:5x) - the owner decides them first: STOP, nothing installed (3.3 E)"; exit 5; }
NOTT=("$FIN/item_alias.py" "$FIN/stockmatch.py" "$FIN/amir_day.py" "$FIN/order_rules.py" "$FIN/qty_words.py" "$SPN/spine_read.py" "$FIN/purchase_app.py" "$FIN/order_sheet.py" "$FIN/porders_s454.py" "$FIN/porders.py" "$FIN/darpan_kal.py" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$DMAP")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/14] live pins exact (stock_app 050587df, shelf_figure 183c70fa, stock_watch 0e6a42c4, loss_piles 81ae481e, spine_build 5d8b1f94, selftest_spine fc63d2c6; stock_figure absent); the read-only files at their pins"
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); 3.3 E: no system-written desk row on or after 2026-10-18"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s577.py walk_s577.py stock_figure.py || { say "!! [3/14] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s577.py --finance "$FIN" --kit "$KDIR" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/14] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED $NEWF; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/14] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for n in $SPINEF; do [ "$(m5 "$SCR/built/spine/$n")" = "${TO[$n]}" ] || { say "!! [4/14] rebuilt, spine/$n is $(m5 "$SCR/built/spine/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED $NEWF; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/14] the built $n does not compile on $py - nothing installed"; exit 1; }; done
  for n in $SPINEF; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/spine/$n" || { say "!! [3/14] the built spine/$n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[3/14] the kit's python files and the seven built files compile on $APY and $VPY"
say "[4/14] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each file at its TO pin; stock_figure.py = the kit's copy"

copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" || { say "!! [5/14] no copy of the databases - nothing installed"; exit 1; }
mkdir -p "$SCR/readings" && cp -p "$SPN"/readings/*.json "$SCR/readings/" || { say "!! [5/14] no copy of the readings - nothing installed"; exit 1; }
mkside() {   # $1 = side: a copy of the live finance code (spine folder included), the ingest reader, the databases
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  cp -p "$SCR/base.db" "$d/f.db" && cp -p "$SCR/base_a.db" "$d/a.db"
}
for side in new old; do mkside "$side" || { say "!! [5/14] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED $NEWF; do cp -p "$SCR/built/$n" "$SCR/new/finance/"; done
for n in $SPINEF; do cp -p "$SCR/built/spine/$n" "$SCR/new/finance/spine/"; done
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
# the scratch spines: the NEW builder and the OLD builder on the same readings copy (R3-C13), the gate 13/13, the selftest
( cd "$SCR/new/finance/spine" && timeout 900 "$VPY" -B spine_build.py --readings "$SCR/readings" --out "$SCR/spine_new.db" --finance-db "$SCR/base.db" > "$SCR/spine_new.txt" 2>&1 ) || { tail -5 "$SCR/spine_new.txt"; say "!! [5/14] the NEW builder failed on the readings copy - nothing installed"; exit 1; }
( cd "$SCR/old/finance/spine" && timeout 900 "$VPY" -B spine_build.py --readings "$SCR/readings" --out "$SCR/spine_old.db" --finance-db "$SCR/base.db" > "$SCR/spine_old.txt" 2>&1 ) || { tail -5 "$SCR/spine_old.txt"; say "!! [5/14] the OLD builder failed on the readings copy - nothing installed"; exit 1; }
HN="$(closehash "$SCR/spine_new.db")"; HO="$(closehash "$SCR/spine_old.db")"
[ "$HN" = "$HO" ] || { say "!! [5/14] sp_close differs between the NEW ($HN) and the OLD ($HO) builder on the same readings - nothing installed"; exit 1; }
GN="$("$APY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print('%d/%d' % c.execute('SELECT SUM(ok), COUNT(*) FROM sp_gate WHERE blocking=1').fetchone()); print(c.execute('SELECT COUNT(*), COUNT(DISTINCT md5) FROM sp_close_name').fetchone())" "$SCR/spine_new.db" | tr '\n' ' ')"
case "$GN" in 13/13*) ;; *) say "!! [5/14] the NEW builder's gate is $GN, not 13/13 - nothing installed"; exit 1;; esac
( cd "$SCR/new/finance/spine" && timeout 600 "$VPY" -B selftest_spine.py > "$SCR/selftest.txt" 2>&1 ) && grep -q "^SELFTEST OK" "$SCR/selftest.txt" || { tail -3 "$SCR/selftest.txt"; say "!! [5/14] selftest_spine red - nothing installed"; exit 1; }
cp -p "$SCR/spine_new.db" "$SCR/new/finance/spine/spine.db"; cp -p "$SCR/spine_new.db" "$SCR/old/finance/spine/spine.db"
say "[5/14] scratch: the finance folder twice (NEW with the seven built files, OLD as it is), the databases, the readings; the spine by the NEW builder = the OLD builder's sp_close ($HN); gate $GN; $(tail -1 "$SCR/selftest.txt")"
mkdir -p "$SCR/oldpy"; for n in $EDITED; do cp -p "$FIN/$n" "$SCR/oldpy/"; done
ROUT="$( cd /tmp && timeout 3000 "$APY" -B "$KDIR/walk_s577.py" --fin "$SCR/old/finance" --old "$SCR/oldpy" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --portal "$SCR/por" --map "$DMAP" --readings "$SCR/readings" --spine-old "$SCR/spine_old.db" --dump "$SCR/dump_old" --expect-red 2>&1 )"; RRC=$?
cp -p "$SCR/spine_new.db" "$SCR/new/finance/spine/spine.db"
WOUT="$( cd /tmp && timeout 3000 "$APY" -B "$KDIR/walk_s577.py" --fin "$SCR/new/finance" --old "$SCR/oldpy" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --portal "$SCR/por" --map "$DMAP" --readings "$SCR/readings" --spine-old "$SCR/spine_old.db" --dump "$SCR/dump_new" --old-dump "$SCR/dump_old" 2>&1 )"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S577"; then say "!! [6/14] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/14] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/14] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
for n in $SPINEF; do [ "$(m5 "$SPN/$n")" = "${FROM[$n]}" ] || { say "!! [6/14] $SPN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[6/14] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch spines and both walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW files (fresh copies of the live database); a flip or a moved A.pending = STOP ----------
statelook() {   # $1 = side folder, $2 = label: the state by that folder's files on a fresh copy of the live database
  local d="$SCR/st_$2"; mkdir -p "$d"; copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s577.py" --state --label "$2" --fin "$1" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --map "$DMAP" 2>&1 ) | mask
}
say "[7/14] the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy:"
SB="$(statelook "$SCR/old/finance" before)"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new)"; echo "$SN" | grep -E "^STATE new:|^   HELD|^   offered|^   unread" | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S577" && echo "$SN" | grep -q "^STATE OK S577" || { say "!! [7/14] the install-day state could not be read - nothing placed"; exit 1; }
FLIP="$("$APY" -c "
import json,sys
b=json.load(open(sys.argv[1])); n=json.load(open(sys.argv[2]))
out=[]
if b['pending']!=n['pending']: out.append('A.pending %s -> %s' % (b['pending'], n['pending']))
if b['offered']!=n['offered']: out.append('offered lines differ: %s -> %s' % (b['offered'], n['offered']))
if b['held']!=n['held']: out.append('held lines differ: %s -> %s' % (b['held'], n['held']))
if b['held_batches']!=n['held_batches']: out.append('held batches differ: %s -> %s' % (b['held_batches'], n['held_batches']))
print('; '.join(out))" "$SCR/st_before/state_before.json" "$SCR/st_new/state_new.json")"
[ -z "$FLIP" ] || { say "!! [7/14] a voucher line flips or A.pending moves between the old and the new files: $FLIP - STOP before placing (3.3 A)"; exit 6; }
say "       no voucher line flips and A.pending stands: the new files judge today's lines as the old ones do"
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/14] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups ---------------------------------------------------------------------------------------------------------------------------
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/14] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [8/14] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [8/14] the backup of $n is not the live file - nothing placed"; exit 1; }
done
for n in $SPINEF; do
  \cp -p "$SPN/$n" "$(sbak $n)" || { say "!! [8/14] backup of spine/$n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(sbak $n)")" = "${FROM[$n]}" ] || { say "!! [8/14] the backup of spine/$n is not the live file - nothing placed"; exit 1; }
done
say "[8/14] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak $n)")"; done)$(for n in $SPINEF; do printf 'spine/%s ' "$(basename "$(sbak $n)")"; done)"

# ---- 9: THE SPINE FIRST --------------------------------------------------------------------------------------------------------------------
LIVE_H0="$(closehash "$SPN/spine.db")"
for n in $SPINEF; do
  { \cp -p "$SPN/$n" "$SPN/.$n.s577" && cat "$SCR/built/spine/$n" > "$SPN/.$n.s577" && [ "$(m5 "$SPN/.$n.s577")" = "${TO[$n]}" ]; } || { rm -f "$SPN"/.*.s577; say "!! [9/14] could not stage spine/$n - nothing placed"; exit 1; }
done
SPINE_PLACED=1
mv -f "$SPN/.spine_build.py.s577" "$SPN/spine_build.py" && mv -f "$SPN/.selftest_spine.py.s577" "$SPN/selftest_spine.py" || restore_spine "placing the spine files"
for n in $SPINEF; do [ "$(m5 "$SPN/$n")" = "${TO[$n]}" ] || restore_spine "spine/$n did not land at its pin"; done
T9="$(date '+%Y-%m-%d %H:%M:%S')"
( cd "$SPN" && timeout 1200 flock -w 300 /tmp/spine.lock sh -c "$VPY -B spine_evidence.py && $VPY -B spine_build.py --readings readings --out spine.db --finance-db $DB" > "$SCR/live_build.txt" 2>&1 ) || { tail -6 "$SCR/live_build.txt" | mask; restore_spine "the live build by the cron command failed (rc $?)"; }
grep -q "SPINE BUILT AND SWAPPED" "$SCR/live_build.txt" || { tail -6 "$SCR/live_build.txt" | mask; restore_spine "the live build did not swap"; }
SP_OK2="$(jget "$SPN/spine_state.json" passed)"; SP_GATE2="$(jget "$SPN/spine_state.json" gate)"
CN="$("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print('%d rows %d captures' % c.execute('SELECT COUNT(*), COUNT(DISTINCT md5) FROM sp_close_name').fetchone())" "$SPN/spine.db" 2>/dev/null || echo "0 rows 0 captures")"
[ "$SP_OK2" = True ] && [ "$SP_GATE2" = "13/13" ] && [ "${CN%% *}" -gt 0 ] || restore_spine "after the live build: passed $SP_OK2, gate $SP_GATE2, sp_close_name $CN"
# R3-C13: sp_close equals a build of the SAME input md5 list by the OLD builder (the readings as they stand now, the backup's builder)
mkdir -p "$SCR/rd2" && cp -p "$SPN"/readings/*.json "$SCR/rd2/" && mkdir -p "$SCR/oldb" && cp -p "$(sbak spine_build.py)" "$SCR/oldb/spine_build.py" && cp -p "$SPN"/spine_rules.json "$SPN"/spine_read.py "$SCR/oldb/" || restore_spine "no copy for the old-builder check"
( cd "$SCR/oldb" && timeout 900 "$VPY" -B spine_build.py --readings "$SCR/rd2" --out "$SCR/spine_old2.db" --finance-db "$DB" > "$SCR/spine_old2.txt" 2>&1 ) || restore_spine "the old builder failed on the live readings"
LIVE_H="$(closehash "$SPN/spine.db")"; OLD_H="$(closehash "$SCR/spine_old2.db")"
[ "$LIVE_H" = "$OLD_H" ] || restore_spine "sp_close of the live spine ($LIVE_H) differs from the old builder's on the same readings ($OLD_H)"
SPINE_PLACED=0
say "[9/14] THE SPINE FIRST: spine_build.py and selftest_spine.py placed; the live build at $T9 by the cron command (flock -w 300) swapped; gate $SP_GATE2; sp_close_name $CN; sp_close = the old builder's on the same readings ($LIVE_H; before the build $LIVE_H0)"

# ---- 10-11: the rest in ONE move, one restart ---------------------------------------------------------------------------------------------
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [10/14] could not write $OFFSW - nothing placed"; exit 1; }
for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s577" && cat "$SCR/built/$n" > "$FIN/.$n.s577" && [ "$(m5 "$FIN/.$n.s577")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s577 "$OFFSW"; say "!! [10/14] could not stage $n - nothing placed (the spine files stay placed: additive)"; exit 1; }
done
{ cat "$SCR/built/$NEWF" > "$FIN/.$NEWF.s577" && chmod 644 "$FIN/.$NEWF.s577" && [ "$(m5 "$FIN/.$NEWF.s577")" = "${TO[$NEWF]}" ]; } || { rm -f "$FIN"/.*.s577 "$OFFSW"; say "!! [10/14] could not stage $NEWF - nothing placed"; exit 1; }
PLACED=1
mv -f "$FIN/.stock_figure.py.s577" "$FIN/stock_figure.py" && mv -f "$FIN/.stock_app.py.s577" "$FIN/stock_app.py" && mv -f "$FIN/.shelf_figure.py.s577" "$FIN/shelf_figure.py" && mv -f "$FIN/.stock_watch.py.s577" "$FIN/stock_watch.py" && mv -f "$FIN/.loss_piles.py.s577" "$FIN/loss_piles.py" || restore "placing the five files"
for n in $EDITED $NEWF; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[10/14] placed by rename in ONE command; md5 read back: $(for n in $NEWF $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/amir); c3=$(health /finance/stock/page/now); c4=$(health /finance/stockmatch); c5=$(health /finance/stock/page/loss)
for c in "$c2" "$c3" "$c4" "$c5"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): amir $c2 / now $c3 / stockmatch $c4 / loss $c5";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
rm -f "$OFFSW"
say "[11/14] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/amir $c2, /stock/page/now $c3, /stockmatch $c4, /stock/page/loss $c5 without a login (302 = the login gate, expected) - journal clean - $OFFSW removed"

# ---- 12: the state AFTER (the live files on a copy), nothing else moved ----------------------------------------------------------------------
say "[12/14] the install-day state AFTER placing (the live files, a fresh copy of the live database):"
SA_="$(statelook "$FIN" after)"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S577" || restore "the state after placing could not be read"
FLIP2="$("$APY" -c "
import json,sys
b=json.load(open(sys.argv[1])); n=json.load(open(sys.argv[2]))
out=[]
if b['pending']!=n['pending']: out.append('A.pending %s -> %s' % (b['pending'], n['pending']))
if b['offered']!=n['offered']: out.append('offered: %s -> %s' % (b['offered'], n['offered']))
if b['held']!=n['held']: out.append('held: %s -> %s' % (b['held'], n['held']))
print('; '.join(out))" "$SCR/st_before/state_before.json" "$SCR/st_after/state_after.json")"
[ -z "$FLIP2" ] || restore "a voucher line flipped after placing: $FLIP2"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
say "       no voucher line flipped, A.pending stands; nothing else moved (the read-only files, finance_app, portal.py, tile_grants.json, DUTY_MAP, the crontab); healthz 200"

# ---- 13-14: the first witness file, the md5s ---------------------------------------------------------------------------------------------
WIT="$( cd "$FIN" && timeout 600 "$VPY" -B stock_figure.py witness 2>&1 | mask )"
say "[13/14] $WIT"
WF="$(echo "$WIT" | sed -n 's/^stock_figure witness written: //p')"
[ -n "$WF" ] && [ -f "$WF" ] && { say "       $(sed -n 2,3p "$WF" | mask | tr '\n' ' ')"; say "       $(grep -E '^marg\(\) vs|^marg_shadow' "$WF" | tr '\n' ' ')"; }
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[14/14] md5 read back:"
for n in $NEWF $EDITED; do md5sum "$FIN/$n"; done
for n in $SPINEF; do md5sum "$SPN/$n"; done
say "$KIT: DONE. The build lock stays held by $KIT until the report is written."
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)rm -f $FIN/$NEWF && $(for n in $SPINEF; do printf '\\cp -p %s %s && ' "$(sbak $n)" "$SPN/$n"; done)$SYSTEMCTL restart $SVC   (sp_close_name, s577_shelf_gap, stock_point.basis stay: additive)"
exit 0
