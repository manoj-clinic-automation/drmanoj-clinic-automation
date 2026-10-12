#!/bin/bash
# =============================================================================
#  install_S539_NORTIMER_OUT.sh · kit S539_NORTIMER_OUT (Sanjeevni, session 310; the owner's word of 12-Oct 08:42 IST; F-185)
#  A DATA-ONLY kit: voucher 11 (count 1, round 2, ISSUE, batch 10) voided; NORTIMER TAB settled for count 1; the other five lines re-made as a
#  new voucher through stock_app._voucher_make. No live file is edited, no service restarted, the clone is not pulled.
#
#  Run by (on the VPS, from the kit folder copied to /root/deploy/kits/S539_NORTIMER_OUT):  bash install_S539_NORTIMER_OUT.sh
#  DRY=1 : gates, the walk on scratch copies -- nothing written, no lock.
#  ORDER (the brief's section 4): gate 0 (SUMS, KIT_ID) · the lock · gates (flask, the databases, the SIX pins read, never edited; the spine
#  passed -- charter 1b) · scratch copies · the walk (DRY stops) · the state BEFORE · finance.db.bak_S539_<stamp> · data_s539.py · the state
#  AFTER · healthz 200 (no restart) · the six pins and the crontab unmoved.
#  A STOP of the data step after its void and settle leaves them (the owner decides, the report says so); nothing is undone by hand.
# =============================================================================
set -u
KIT="S539_NORTIMER_OUT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SPN=$FIN/spine; REPO=/root/deploy/repo
DBF="$FIN/finance.db"; SPD="$SPN/spine.db"; DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s539_walk_$STAMP"
declare -A PIN=( ["$FIN/stock_app.py"]=f58e09dbb273e8b1470aa7220da70015 ["$FIN/stock_watch.py"]=0e6a42c4c7ae51eb8f8a0869fce2d101
                 ["$FIN/shelf_figure.py"]=183c70fabb64ed1e5a43c645a225c560 ["$FIN/loss_piles.py"]=81ae481e4480a12fead3016515037214
                 ["$FIN/stock_statement.py"]=a90f3413427841b7daea76b7730b2896 ["$DMAP"]=f499dd1fb53cb9b23422154aac41596e )
mkdir -p "$WALK/noring" || exit 1
export ORDER_PUSH_STUB="$WALK/installer_pushes.jsonl" RING_PORTAL_DIR="$WALK/noring" REPORTS_NTFY_STUB="$WALK/installer_ntfy_stub.jsonl"
unset ORDER_PUSH_NONE ORDER_TODAY ORDER_TICK ORDER_CLOCK
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$SPY" -c "import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$1" "$2" 2>/dev/null; }
bail() { say "$1"; rm -rf "$WALK"; exit "${2:-1}"; }
state_print() { ( cd "$FIN" && SPINE_DB="$SPD" timeout 900 "$SPY" -B "$KDIR/data_s539.py" --db "$DBF" --finance "$FIN" --state 2>&1 ) | mask | cut -c1-500 | sed 's/^/   /'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/9] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/9] KIT_ID.txt names another kit - nothing done"; exit 1; }
# ---- 1: the lock
if [ "${DRY:-0}" = 1 ]; then say "[1/9] DRY RUN: no lock, no backup, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/9] the build lock is already held by $KIT"
else say "!! [1/9] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates
"$VPY" -c "import flask" 2>/dev/null || bail "!! [2/9] the venv python lacks flask (the walk); nothing written"
"$SPY" -c "import flask" 2>/dev/null || bail "!! [2/9] the service python lacks flask; nothing written"
for k in "$DBF" "$SPD" "$SPN/spine_state.json"; do [ -e "$k" ] || bail "!! [2/9] $k must be reachable - nothing written"; done
for f in "${!PIN[@]}"; do [ "$(m5 "$f")" = "${PIN[$f]}" ] || bail "!! [2/9] $f is $(m5 "$f"), not its pin ${PIN[$f]} (S537's TO) - STOP, nothing written"; done
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] || bail "!! [2/9] the spine is red (passed $SP_OK, gate $SP_GATE) - nothing written (charter 1b)" 4
CRON0="$(cron5)"
say "[2/9] gates green (SUMS, KIT_ID, flask, the databases); the six pins read (S537's TOs, never edited here); the spine passed $SP_GATE (last success $SP_AT)"
# ---- 3-4: scratch copies, the walk
R="$WALK/run"; mkdir -p "$R/finance/spine" "$R/finance/finance_ui" || exit 1
cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/finance/" 2>/dev/null; cp -rp "$FIN/finance_ui/." "$R/finance/finance_ui/"
cp -p "$SPN"/*.py "$SPN"/*.json "$R/finance/spine/" 2>/dev/null
copydb "$DBF" "$R/scratch.db" && copydb "$SPD" "$R/scratch_spine.db" || bail "!! [3/9] no scratch copies - nothing written"
say "[3/9] scratch copies: the finance folder; finance.db and the LIVE spine.db by the backup API"
WOUT="$( cd "$R" && timeout 3600 "$VPY" -B "$KDIR/walk_s539.py" --kit "$KDIR" --work "$R/w" --finance "$R/finance" --db "$R/scratch.db" --spine "$R/scratch_spine.db" --map "$DMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1600 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S539 GREEN" || bail "!! [4/9] walk_s539 red - nothing written"
say "[4/9] walk_s539 green on scratch copies; every named control red on the untouched copy (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 5-6: the state before, the backup
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || bail "!! [5/9] the build lock is not held by $KIT - nothing written"
for f in "${!PIN[@]}"; do [ "$(m5 "$f")" = "${PIN[$f]}" ] || bail "!! [5/9] $f moved during the walk - nothing written"; done
say "[5/9] the state BEFORE (a scratch copy of the live database):"
state_print
copydb "$DBF" "$FIN/finance.db.bak_S539_$STAMP" && [ -s "$FIN/finance.db.bak_S539_$STAMP" ] || bail "!! [6/9] database backup failed - nothing written"
say "[6/9] $FIN/finance.db.bak_S539_$STAMP by the backup API ($(stat -c %s "$FIN/finance.db.bak_S539_$STAMP") bytes)"
# ---- 7: the data step
DOUT="$( cd "$FIN" && SPINE_DB="$SPD" timeout 1800 "$SPY" -B "$KDIR/data_s539.py" --db "$DBF" --finance "$FIN" 2>&1 )"; DRC=$?
echo "$DOUT" | mask | cut -c1-400 | sed 's/^/   /'
if [ "$DRC" != 0 ] || ! echo "$DOUT" | grep -q -E "^DATA_S539: (committed|ALREADY DONE)"; then
  say "!! [7/9] the data step did not finish (exit $DRC) -- what it committed stays (the owner decides); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  rm -rf "$WALK"; exit 1
fi
say "[7/9] the data step ran on the live database (above)"
# ---- 8-9: the state after, health, nothing moved
say "[8/9] the state AFTER (a scratch copy of the live database):"
state_print
c1=$(health http://127.0.0.1:8106/finance/healthz)
for f in "${!PIN[@]}"; do [ "$(m5 "$f")" = "${PIN[$f]}" ] || { say "!! $f moved"; c1=moved; }; done
[ "$(cron5)" = "$CRON0" ] || { say "!! the crontab moved"; c1=moved; }
[ "$c1" = 200 ] || { say "!! [9/9] finance healthz $c1 after the data step -- said for the report"; rm -rf "$WALK"; exit 1; }
say "[9/9] finance healthz 200 (no restart: no code moved); the six pins and the crontab unmoved; backup $FIN/finance.db.bak_S539_$STAMP · the lock stays held by $KIT until the report is written"
rm -rf "$WALK"
say "$KIT: DONE"
