#!/bin/bash
# =============================================================================
#  install_S602_CUTOFF_LINE_AND_F943.sh · kit S602 (19-Oct-2026) · brief claude_code_briefs/S602_CUTOFF_LINE_AND_F943.md (v2) · D746, closes F-943
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S602_CUTOFF_LINE_AND_F943), 08:00-23:49 IST only:
#    rm -rf /tmp/s602kit && cp -rp <kit> /tmp/s602kit && bash /tmp/s602kit/install_S602_CUTOFF_LINE_AND_F943.sh
#  (DRY=1 before bash: every gate, the scratch sides and the walks, nothing written, no lock.)
#
#  D746: one grey line under the heading of Darpan's order tab -- "Marg में खरीद dd-mm के बिल तक चढ़ी है ..." -- the newest purchase-bill day
#  Marg's purchases hold, read through the spine's one door and served by the tab's own payload. F-943: the nightly witness's read-only
#  run no longer meets the start-capture judge (Ctx.read_only, read by _may_write alone).
#   /root/finance/spine/spine_read.py  827b0040 -> TO   purchases_upto() (MAX(date) of PURCHASE bills dated <= today, or None); one docstring line
#   /root/finance/darpan_kal.py        325d988c -> TO   _s485_payload carries purchase_upto (a fresh spine handle, closed; None when the spine cannot open)
#   /root/finance/darpan_kal.html      75d5a5b5 -> TO   renderOrder's heading: the one fragment (line 427)
#   /root/finance/stock_figure.py      cb577821 -> TO   Ctx(read_only=), _may_write(con, ctx), witness() read-only; KIT = S602
#  No DDL, no new table, no new setting, no data step. Read only, must not move (this kit was built reading them): order_rules, stock_watch,
#  order_sheet, porders, porders_s454, shelf_figure, stock_app, amir_day, spine/spine_build; proved unmoved: finance_app, portal.py, the
#  crontab (84 lines, S577_WITNESS once), spine.db's schema. No duty added, moved or removed (DUTY_MAP untouched).
#  ORDER: gates (window, lock, SUMS, KIT_ID, PINS) -> pins (ALREADY first) + the read-only md5s + the crontab -> the spine green and fresh ->
#  the witness log's tail (F-510: the clock is read) and the newest witness file's header -> build from the live bytes (anchored edits,
#  each anchor once) -> compile (both pythons) and the JS check of the built html -> scratch: the finance folder twice, finance.db / assets.db /
#  spine.db by the backup API; the walk on the OLD files (every control red) then on the NEW files (green); S598's walk on both sides, its
#  check lines equal -> DRY stops -> the install-day state BEFORE (the OLD files on a copy) and as the NEW files read the same copy ->
#  backups -> DOCTOR_AUTO_OFF -> the FOUR files staged and renamed in ONE command -> ONE restart of clinic-finance -> healthz 200, the pages
#  302 -> journal clean -> the state AFTER (the live files on a fresh copy: purchase_upto present, the capture rows unchanged) -> the witness
#  run ONCE on live, read-only, as the crontab runs it (stderr must be empty; it overwrites today's witness file, which 23:58 overwrites
#  again) -> nothing else moved -> md5 read-back -> DOCTOR_AUTO_OFF removed. Red after placing: the four files put back in one command,
#  one restart, healthz. The build lock stays held until the report is written. Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S602_CUTOFF_LINE_AND_F943"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
S598KIT="${S598KIT:-/root/deploy/repo/deploy_kits/S598_ARRIVALS_BY_LINE}"
WLOG="${WLOG:-$SPN/stock_figure_witness.log}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDITED="darpan_kal.py darpan_kal.html spine/spine_read.py stock_figure.py"
declare -A FROM TO READ
FROM[darpan_kal.py]=325d988c61e1c7408a2a4b687a4822bb
FROM[darpan_kal.html]=75d5a5b51b017abd5ad3aa408609a1ff
FROM[spine/spine_read.py]=827b00402add288d028c910128084b90
FROM[stock_figure.py]=cb577821d9e1eb40110312b4331df9ef
READ[order_rules.py]=8d078dbe1b63a4706dc6f35e3c31ac9a
READ[stock_watch.py]=299c3ef76b73a10e4af1cd15974c7a3f
READ[order_sheet.py]=1f1e85c12c64521b50a10cea48220170
READ[porders.py]=e5a5c4d4dfa15c3ecd0b0cdf4786abcd
READ[porders_s454.py]=40f1755a7655deb733765456b9a466fe
READ[shelf_figure.py]=23b2394a7a10a99ff0c30121087813f1
READ[stock_app.py]=4f73d0b02a167289d9439af7a35b5fa0
READ[amir_day.py]=3af992d9e6b6c6050b1427e34757ca78
READ[spine/spine_build.py]=e3d3ed85973eab2df0326dc9621e230e
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s602_inst_$STAMP"
PLACED=0
DBBAK="$FIN/finance.db.bak_S602_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S602_${FROM[$1]:0:8}"; }
stg() { echo "$FIN/$(dirname "$1")/.$(basename "$1").s602" | sed 's#/\./#/#'; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
schema5() { "$APY" -c "import sqlite3,sys,hashlib; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(hashlib.md5('\n'.join(sorted(r[0] or '' for r in c.execute(\"SELECT sql FROM sqlite_master WHERE type IN ('table','index')\"))).encode()).hexdigest())" "$1" 2>/dev/null; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
live_pu() { "$APY" -c "import sqlite3,sys,datetime as d; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(c.execute(\"SELECT MAX(date) FROM sp_purchase_bill WHERE direction='PURCHASE' AND date<=?\",(d.date.today().isoformat(),)).fetchone()[0])" "$1" 2>/dev/null; }
caprows() { "$APY" -c "import sqlite3,sys,datetime as d; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); r=(d.date.today()-d.timedelta(days=21)).isoformat(); [print('   ', x[0][:8], 'printed', x[1], 'taken', x[2], '-> end', x[3], ':', x[4], ('/ '+x[5]) if x[5] else '', '(checked', str(x[6])+')') for x in c.execute('SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso', (r,))]" "$1" 2>/dev/null; }
caprows5() { "$APY" -c "import sqlite3,sys,datetime as d,hashlib; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); r=(d.date.today()-d.timedelta(days=21)).isoformat(); print(hashlib.md5(repr(c.execute('SELECT md5, as_on, stamp_iso, end_day, verdict FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso', (r,)).fetchall()).encode()).hexdigest())" "$1" 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the four files back in one command"
  \cp -p "$(bak darpan_kal.py)" "$FIN/darpan_kal.py" && \cp -p "$(bak darpan_kal.html)" "$FIN/darpan_kal.html" && \cp -p "$(bak spine/spine_read.py)" "$SPN/spine_read.py" && \cp -p "$(bak stock_figure.py)" "$FIN/stock_figure.py"
  rm -f "$FIN"/.*.s602 "$SPN"/.*.s602
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK"
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
{ [ "$HH" -ge 8 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } || { say "!! [1/12] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:00-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/12] $FIN/$n is not there - nothing installed"; exit 1; }; done
[ -f "$S598KIT/walk_s598.py" ] && ( cd "$S598KIT" && md5sum -c SUMS.md5 >/dev/null 2>&1 ) || { say "!! [1/12] S598's kit is not at $S598KIT or fails its SUMS (its walk is run on the NEW files) - nothing installed"; exit 1; }
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the four files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, S598's kit, the window); no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green (SUMS, KIT_ID, PINS, S598's kit, the window); the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi

for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; exit 1; }; done
say "[2/12] live pins exact: $(for n in $EDITED; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)"
say "       the read-only files' live md5s (the brief, section 1):"
for n in order_rules.py stock_watch.py order_sheet.py porders.py porders_s454.py shelf_figure.py stock_app.py amir_day.py spine/spine_build.py; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }
done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] || { say "!! [2/12] a database or the spine is missing - nothing installed"; exit 1; }
CRONN="$(crontab -l 2>/dev/null | wc -l | awk '{print $1}')"; CRONW="$(crontab -l 2>/dev/null | grep -c S577_WITNESS || true)"
say "       the crontab: $CRONN lines, S577_WITNESS lines ${CRONW:-0}: $(crontab -l 2>/dev/null | grep S577_WITNESS | sed -E 's/^([0-9]+ [0-9]+) .*/\1 (min hour) .../')"
[ "$CRONN" = 84 ] && [ "${CRONW:-0}" = 1 ] || { say "!! [2/12] the crontab is not as the brief read it (84 lines, S577_WITNESS once) - STOP, nothing installed"; exit 1; }
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - the kit depends on it; nothing installed (charter 1b)"; exit 4; }
NOTT=("$FIN/order_rules.py" "$FIN/stock_watch.py" "$FIN/order_sheet.py" "$FIN/porders.py" "$FIN/porders_s454.py" "$FIN/shelf_figure.py" "$FIN/stock_app.py" "$FIN/amir_day.py" "$SPN/spine_build.py" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"; SCHEMA0="$(schema5 "$SPN/spine.db")"
[ -n "$SCHEMA0" ] || { say "!! [2/12] the spine's schema could not be read - nothing installed"; exit 1; }
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago); spine.db schema $SCHEMA0"
say "       the live spine's purchases_upto (MAX(date) of PURCHASE bills dated <= today, read only): $(live_pu "$SPN/spine.db")"
say "       order.source / darpan_list_time: $("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print(dict(c.execute(\"SELECT key, value FROM setting WHERE key IN ('order.source','order.darpan_list_time','count.start_capture') ORDER BY key\").fetchall()))" "$DB")"
say "       stock_start_capture rows within LATE_DAYS (21) on the live database (read only):"
caprows "$DB"
CAP0="$(caprows5 "$DB")"
say "       F-510, the clock read: the witness log $WLOG (the crontab's 2>&1 target):"
if [ -f "$WLOG" ]; then tail -n 20 "$WLOG" | mask | sed 's/^/         | /'; else say "         (not yet written: the crontab appends to it at 23:58 and no night has run since S594's install -- the first real night is tonight)"; fi
WNEW="$(ls -t "$SPN"/stock_figure_witness_*.txt 2>/dev/null | head -1)"
[ -n "$WNEW" ] && say "       the newest witness file $(basename "$WNEW") (mtime $(date -r "$WNEW" '+%Y-%m-%d %H:%M:%S')): $(head -n 1 "$WNEW")" || say "       no witness file in $SPN"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s602.py walk_s602.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s602.py --finance "$FIN" --out "$SCR/built" > "$SCR/make.txt" || { cat "$SCR/make.txt"; say "!! [4/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in darpan_kal.py spine/spine_read.py stock_figure.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/12] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
JS="$("$APY" -B walk_s602.py --jscheck "$SCR/built/darpan_kal.html" 2>&1)" || { say "$JS"; say "!! [3/12] the built darpan_kal.html fails the JS check - nothing installed"; exit 1; }
say "[3/12] the kit's python files and the three built python files compile on $APY and $VPY; $JS"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits): each of the four files at its TO pin"

copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine.db" || { say "!! [5/12] no copy of the databases - nothing installed"; exit 1; }
mkside() {   # $1 = side: a copy of the live finance code (spine folder included), the ingest reader, the databases (backup API), the spine copy
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  cp -p "$SCR/base.db" "$d/f.db" && cp -p "$SCR/base.db" "$d/f598.db" && cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/spine.db" "$d/finance/spine/spine.db"
}
for side in new old; do mkside "$side" || { say "!! [5/12] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/$n"; done
say "[5/12] scratch: the finance folder twice (NEW with the four built files, OLD as it is), finance.db (twice: the walk's and S598's walk's), assets.db and the spine by the backup API"
ROUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s602.py" --fin "$SCR/old/finance" --db "$SCR/old/f.db" --adb "$SCR/old/a.db" --marg "$SCR/old/marg_ingest" --dump "$SCR/dump_old" --expect-red 2>&1 )"; RRC=$?
WOUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s602.py" --fin "$SCR/new/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --dump "$SCR/dump_new" --old-dump "$SCR/dump_old" 2>&1 )"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S602"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED|^WALK RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/12] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S602: //')"
say "       S598's walk (walk_s598.py, whole) on the NEW files and on the OLD files -- its check lines must be the same on both (the kit changes nothing it sees):"
w598() { ( cd /tmp && timeout 2400 "$APY" -B "$S598KIT/walk_s598.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f598.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --kit "$S598KIT" --dump "$SCR/dump598_$1" 2>&1 ); }
W598N="$(w598 new)"; W598O="$(w598 old)"
find "$S598KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
# the two lines that MUST differ: the tab page's byte count (the html grew by the fragment) and S598's own 'KIT = "S598' check (the kit line is S602's now)
w598lines() { grep -E '^  (ok|FAIL) ' | grep -v 'KIT = "S598' | sed -E 's/[0-9]+\.[0-9]s/N.Ns/g; s/\(200, [0-9]+ bytes\)/(200, N bytes)/'; }
echo "$W598N" | w598lines > "$SCR/w598_new.txt"
echo "$W598O" | w598lines > "$SCR/w598_old.txt"
say "         NEW: $(echo "$W598N" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-60)... ($(grep -c '^  FAIL ' "$SCR/w598_new.txt") FAIL line(s) beside its KIT line)"
say "         OLD: $(echo "$W598O" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-60)... ($(grep -c '^  FAIL ' "$SCR/w598_old.txt") FAIL line(s))"
if ! cmp -s "$SCR/w598_new.txt" "$SCR/w598_old.txt"; then say "!! [6/12] S598's walk reads differently on the NEW files than on the OLD files (beyond the page's byte count and its own KIT line) - nothing installed"; diff "$SCR/w598_old.txt" "$SCR/w598_new.txt" | mask | head -20; exit 1; fi
[ -s "$SCR/w598_new.txt" ] || { say "!! [6/12] S598's walk printed no check line - nothing installed"; exit 1; }
echo "$W598O" | grep -q '^  ok   C: KIT = "S598' && echo "$W598N" | grep -q '^  FAIL C: KIT = "S598' || { say "!! [6/12] S598's walk did not see the kit line move (ok on OLD, FAIL on NEW expected) - nothing installed"; exit 1; }
grep '^  FAIL ' "$SCR/w598_new.txt" | mask | cut -c1-150 | sed 's/^/         (both sides, today'"'"'s data: lines 3 and 50 were cleared on live on 19-Oct) /'
say "         S598's walk: $(wc -l < "$SCR/w598_new.txt") check lines identical on both sides; its KIT line ok on OLD and FAIL on NEW (the kit line is S602's); /finance/darpan/kal $(echo "$W598O" | grep -o 'darpan reads /finance/darpan/kal (200, [0-9]* bytes)' | grep -o '[0-9]* bytes') -> $(echo "$W598N" | grep -o 'darpan reads /finance/darpan/kal (200, [0-9]* bytes)' | grep -o '[0-9]* bytes') (the fragment)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch sides and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW files (fresh copies of the live database) ----------------------------------------------
statelook() {   # $1 = a scratch finance folder, or LIVE (a fresh scratch copy of /root/finance as it stands, its spine.db beside it); $2 = label
  local d="$SCR/st_$2" fin="$1"; mkdir -p "$d"
  if [ "$1" = LIVE ]; then
    mkside "st_$2" >/dev/null 2>&1 || return 1
    copydb "$SPN/spine.db" "$d/finance/spine/spine.db" || return 1
    fin="$d/finance"
  fi
  copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s602.py" --state --label "$2" --fin "$fin" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --witness-dir "$SPN" 2>&1 ) | mask
}
say "[7/12] the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy (charter 7):"
SB="$(statelook "$SCR/old/finance" before)"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new)"; echo "$SN" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S602" && echo "$SN" | grep -q "^STATE OK S602" || { say "!! [7/12] the install-day state could not be read - nothing placed"; exit 1; }
PU_NEW="$(echo "$SN" | grep -o '^STATE new: api/order purchase_upto = [0-9-]*' | awk '{print $NF}')"
[ "$PU_NEW" = "$(live_pu "$SPN/spine.db")" ] || { say "!! [7/12] the NEW files' purchase_upto ($PU_NEW) is not the live spine's day ($(live_pu "$SPN/spine.db")) - nothing placed"; exit 1; }
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups ---------------------------------------------------------------------------------------------------------------------------
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/12] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [8/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [8/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[8/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $EDITED; do printf '%s ' "$(bak $n | sed "s#$FIN/##")"; done)"

# ---- 9-10: the four files in ONE move, one restart ------------------------------------------------------------------------------------------
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [9/12] could not write $OFFSW - nothing placed"; exit 1; }
for n in $EDITED; do
  { \cp -p "$FIN/$n" "$(stg $n)" && cat "$SCR/built/$n" > "$(stg $n)" && [ "$(m5 "$(stg $n)")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s602 "$SPN"/.*.s602 "$OFFSW"; say "!! [9/12] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
mv -f "$(stg darpan_kal.py)" "$FIN/darpan_kal.py" && mv -f "$(stg darpan_kal.html)" "$FIN/darpan_kal.html" && mv -f "$(stg spine/spine_read.py)" "$SPN/spine_read.py" && mv -f "$(stg stock_figure.py)" "$FIN/stock_figure.py" || restore "placing the four files"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[9/12] placed by rename in ONE command; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/darpan/kal); c3=$(health /finance/darpan/kal/api/order); c4=$(health /finance/porders); c5=$(health /finance/stockmatch); c6=$(health /finance/amir); c7=$(health /finance/reports/aaj)
for c in "$c2" "$c3" "$c4" "$c5" "$c6" "$c7"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): darpan/kal $c2 / its api/order $c3 / porders $c4 / stockmatch $c5 / amir $c6 / reports-aaj $c7";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/darpan/kal $c2, its api/order $c3, /porders $c4, /stockmatch $c5, /amir $c6, /reports/aaj $c7 without a login (302 = the login gate, expected) - journal clean"

# ---- 11: the state AFTER; the witness once on live, read-only; nothing else moved ------------------------------------------------------------
say "[11/12] the install-day state AFTER placing (the live files, a fresh copy of the live database):"
SA_="$(statelook LIVE after)"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S602" || restore "the state after placing could not be read"
PU_AFTER="$(echo "$SA_" | grep -o '^STATE after: api/order purchase_upto = [0-9-]*' | awk '{print $NF}')"
[ -n "$PU_AFTER" ] && [ "$PU_AFTER" = "$(live_pu "$SPN/spine.db")" ] || restore "api/order after placing does not carry purchase_upto = the live spine's day ($PU_AFTER vs $(live_pu "$SPN/spine.db"))"
CAP1="$(caprows5 "$DB")"
[ "$CAP1" = "$CAP0" ] || say "        note: a stock_start_capture row's verdict moved between the open and now (the day's own pages judge as before; this kit writes no row):"
caprows "$DB"
say "        the witness ONCE on live, read-only, as the crontab runs it (cd $FIN && $VPY -B stock_figure.py witness; it overwrites today's witness file, which 23:58 overwrites again):"
TW="$(date '+%Y-%m-%d %H:%M:%S')"
( cd "$FIN" && timeout 1200 "$VPY" -B stock_figure.py witness > "$SCR/wit.out" 2> "$SCR/wit.err" ); WRC2=$?
say "        exit $WRC2 at $(date '+%Y-%m-%d %H:%M:%S') (started $TW); stdout: $(mask < "$SCR/wit.out" | tr '\n' ' ')"
if [ -s "$SCR/wit.err" ]; then say "        stderr:"; mask < "$SCR/wit.err" | sed 's/^/          | /'; restore "the witness on live wrote to stderr"; else say "        stderr: EMPTY"; fi
[ "$WRC2" = 0 ] || restore "the witness on live exited $WRC2"
WFILE="$(sed -n 's/^stock_figure witness written: //p' "$SCR/wit.out" | head -1)"
[ -n "$WFILE" ] && [ -f "$WFILE" ] || restore "the witness on live did not say which file it wrote"
say "        the file's header: $(head -n 1 "$WFILE" | mask)"
say "        its capture line: $(sed -n 2p "$WFILE" | mask)"
[ "$(caprows5 "$DB")" = "$CAP1" ] || restore "a stock_start_capture row moved during the read-only witness run"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(schema5 "$SPN/spine.db")" = "$SCHEMA0" ] || restore "spine.db's schema moved -- no table may be added to the spine"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, spine_build, the spine's schema, portal.py, tile_grants.json, the crontab); healthz 200; $OFFSW removed"
say "        the ten-minute tick and every page read pick the new files up on their next run; tonight's 23:58 witness runs the new stock_figure"

find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE. The build lock stays held by $KIT until the report is written."
say "undo (the files): \\cp -p $(bak darpan_kal.py) $FIN/darpan_kal.py && \\cp -p $(bak darpan_kal.html) $FIN/darpan_kal.html && \\cp -p $(bak spine/spine_read.py) $SPN/spine_read.py && \\cp -p $(bak stock_figure.py) $FIN/stock_figure.py && $SYSTEMCTL restart $SVC"
exit 0
