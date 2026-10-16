#!/bin/bash
# =============================================================================
#  install_S570_PROOF_MORNING_WINDOW.sh · kit S570_PROOF_MORNING_WINDOW (Sanjeevni, session 316; the owner's "yes" of 16-Oct 11:08 IST; F-905, F-906)
#  The voucher proof's reach rule reads an export by the estate's one capture rule (a sale report of the morning covers the closing of the
#  same morning), and the owner's waiting sentence names the closing the proof uses and what it really waits for. stock_app.py only.
#
#  Run by (on the VPS, from the kit folder):  bash install_S570_PROOF_MORNING_WINDOW.sh
#  DRY=1 : gates, build, compile, the walk on scratch copies -- nothing placed, nothing written, no lock.
#  ORDER (the brief's section 4): gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED) · the lock · gates (flask on both pythons, the databases, the FROM
#  pin, the spine passed and not behind the collector, the collector alive -- charter 1b; the must-not-move md5s recorded) · build (make_s570.py)
#  · compile both pythons · scratch copies · the walk + controls (DRY stops) · re-check · the state BEFORE · backups · place by rename · md5
#  read-back · ONE restart of clinic-finance · healthz 200 · the gated pages answer the gate · the journal · the proof read back (state_s570.py)
#  · nothing else moved.  Red after placing -> stock_app.py restored byte-identically, restart, healthz, report. The database backup is kept.
# =============================================================================
set -u
KIT="S570_PROOF_MORNING_WINDOW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SPN=$FIN/spine; ING=/root/marg_ingest; POR=/root/portal
DBF="$FIN/finance.db"; SPD="$SPN/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s570_walk_$STAMP"
SVC=clinic-finance
F=stock_app.py
FROM=f58e09dbb273e8b1470aa7220da70015
declare -A TO
NOTT=("$FIN/amir_day.py" "$FIN/finance_app.py" "$FIN/stock_watch.py" "$FIN/shelf_figure.py" "$FIN/stockmatch.py" "$FIN/sanjeevni_approvals.py"
      "$FIN/stock_hub.html" "$FIN/stock_amir.html" "$FIN/qty_words.py" "$POR/portal.py" "$POR/tile_grants.json" "$SPN/spine_build.py" "$SPN/spine_read.py"
      "$SPN/marg_read.py" "$SPN/spine_rules.json")
mkdir -p "$WALK" || exit 1
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$SPY" -c "import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$1" "$2" 2>/dev/null; }
state_print() {   # the owner's proof on fresh backup-API copies, read by the files in /root/finance as they stand
  ( cd /tmp && timeout 1500 "$VPY" -B "$KDIR/state_s570.py" --finance "$FIN" --work "$WALK/state_$1" 2>&1 ) | mask | cut -c1-900 | sed 's/^/   /'
}
bail() { say "$1"; rm -rf "$WALK"; exit "${2:-1}"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/13] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/13] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/13] PINS.sh missing - nothing done"; exit 1; }
if [ "$(m5 "$FIN/$F")" = "${TO[$F]}" ]; then
  say "-- ALREADY INSTALLED: $FIN/$F is at the kit's TO pin ${TO[$F]}; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  state_print now; rm -rf "$WALK"; exit 0
fi
# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/13] DRY RUN: no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/13] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/13] the build lock is already held by $KIT"
else say "!! [1/13] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates --------------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || bail "!! [2/13] the venv python lacks flask (the walk); nothing placed"
"$SPY" -c "import flask" 2>/dev/null || bail "!! [2/13] the service python lacks flask; nothing placed"
for k in "$DBF" "$SPD" "$SPN/spine_state.json" "$ING/last_run.json" "$FIN/amir_day.py"; do [ -e "$k" ] || bail "!! [2/13] $k must be reachable - nothing placed"; done
[ "$(m5 "$FIN/$F")" = "$FROM" ] || bail "!! [2/13] $FIN/$F is $(m5 "$FIN/$F"), not its FROM pin $FROM - someone changed it since the brief; nothing placed"
# charter 1b: the spine passed (every gate green) and built since the collector's newest take; the collector alive -- S537's rule, unchanged
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
LAG="$("$SPY" -c "
import sqlite3,sys,datetime as d
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
r=c.execute(\"SELECT MAX(received_at) FROM mi_file\").fetchone()[0]
t=d.datetime.fromisoformat(r); s=d.datetime.fromisoformat(sys.argv[2])
print(int((t-s).total_seconds()//60), int((d.datetime.now(t.tzinfo)-t).total_seconds()//3600))" "$DBF" "$SP_AT" 2>/dev/null || echo "9999 9999")"
SP_BEHIND="${LAG% *}"; COL_AGE="${LAG#* }"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_BEHIND" -le 40 ] \
  || bail "!! [2/13] the spine is red or behind the collector (passed $SP_OK, gate $SP_GATE, last success $SP_AT, the newest take $SP_BEHIND min after it) - the kit depends on it; nothing placed (charter 1b)" 4
ING_RUN="$("$SPY" -c "
import json,sys,datetime as d
j=json.load(open(sys.argv[1])); t=d.datetime.fromisoformat(j['finished'])
print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60), int(j.get('failed') or 0))" "$ING/last_run.json" 2>/dev/null || echo "9999 0")"
ING_LOG_AGE="${ING_RUN% *}"; ING_FAILED="${ING_RUN#* }"
[ "$ING_LOG_AGE" -le 30 ] && [ "$COL_AGE" -le 72 ] || bail "!! [2/13] the collector is cold (its last run $ING_LOG_AGE min ago, newest take $COL_AGE h ago); nothing placed (charter 1b)" 4
declare -A NT0
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/13] gates green (SUMS, KIT_ID, PINS, flask on both pythons, the databases); $F at its FROM pin $FROM; the spine passed $SP_GATE (last success $SP_AT, the newest take $SP_BEHIND min after it); the collector last ran $ING_LOG_AGE min ago ($ING_FAILED failed), its newest take $COL_AGE h ago; amir_day.py ${NT0[$FIN/amir_day.py]} (read only)"
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s570.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
[ "$(m5 "$WALK/built/$F")" = "${TO[$F]}" ] || bail "!! [3/13] the built $F is $(m5 "$WALK/built/$F"), not the kit's pin ${TO[$F]} - nothing placed"
say "[3/13] live bytes + the four anchored edits give $F at its TO pin ${TO[$F]}"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && cp -p "$WALK/built/$F" "$WALK/cc/built_$F"
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || bail "!! [4/13] compile on both pythons failed - nothing placed"
rm -rf "$WALK/cc"
say "[4/13] the built file and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 5-6: scratch copies, the walk ------------------------------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance/finance_ui" "$R/$side/finance/spine" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance/finance_ui/"; cp -p "$SPN"/*.py "$SPN"/*.json "$R/$side/finance/spine/" 2>/dev/null
  [ -f "$R/$side/finance/finance_app.py" ] && [ -f "$R/$side/finance/amir_day.py" ] || bail "!! [5/13] no scratch copy of the finance folder - nothing placed"
done
cp -p "$WALK/built/$F" "$R/new/finance/$F"
copydb "$DBF" "$R/scratch.db" && copydb "$SPD" "$R/scratch_spine.db" || bail "!! [5/13] no scratch copies - nothing placed"
say "[5/13] scratch copies: the finance folder twice (NEW with the built $F, OLD as it is); finance.db and the LIVE spine.db by the backup API"
WOUT="$( cd "$R" && timeout 5400 "$VPY" -B "$KDIR/walk_s570.py" --run "$R" --work "$R/w" --db "$R/scratch.db" --spine "$R/scratch_spine.db" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1600 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S570 GREEN" || bail "!! [6/13] walk_s570 red - nothing placed"
say "[6/13] walk_s570 green on scratch copies; every named control red on the old file (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 7-8: re-check, the state before, backups ----------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || bail "!! [7/13] the build lock is not held by $KIT - nothing placed"
[ "$(m5 "$FIN/$F")" = "$FROM" ] || bail "!! [7/13] $FIN/$F moved during the walk - nothing placed"
say "[7/13] the lock is held by $KIT; the FROM pin still stands after the walk"
say "   the owner's proof BEFORE placing (the old file, on backup-API copies of the live databases):"
state_print before
BAK="$FIN/$F.bak_S570_${FROM:0:8}"
\cp -p "$FIN/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || bail "!! [8/13] the backup of $F does not read back - nothing placed"
copydb "$DBF" "$FIN/finance.db.bak_S570_$STAMP" && [ -s "$FIN/finance.db.bak_S570_$STAMP" ] || bail "!! [8/13] database backup failed - nothing placed"
say "[8/13] $BAK ($(m5 "$BAK")); $FIN/finance.db.bak_S570_$STAMP by the backup API ($(stat -c %s "$FIN/finance.db.bak_S570_$STAMP") bytes)"
putfile() { \cp -p "$1" "$2.s570_new" && mv -f "$2.s570_new" "$2"; }
restore() {
  say "!! RED after placing ($1) - restoring $F byte-identically (the database backup is kept; this kit writes no data)"
  putfile "$BAK" "$FIN/$F"
  systemctl restart "$SVC" || true; sleep 8
  say "   $FIN/$F $(m5 "$FIN/$F") (FROM $FROM)"
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC")"
  rm -rf "$WALK"; exit 1
}
# ---- 9: place, read back ------------------------------------------------------------------------------------------------------------------
putfile "$WALK/built/$F" "$FIN/$F" || restore "copy $F"
[ "$(m5 "$FIN/$F")" = "${TO[$F]}" ] || restore "md5 read-back $F"
cmp -s "$FIN/$F" "$R/new/finance/$F" || restore "the placed file is not the walk's file"
G1="$(grep -c '_s570_covers(' "$FIN/$F")"; G2="$(grep -c '_s570_push_end(' "$FIN/$F")"
say "[9/13] $F placed by rename; md5 read back $(m5 "$FIN/$F") = its TO pin; byte-identical to the walk's NEW copy; greps _s570_covers( $G1 · _s570_push_end( $G2"
[ "$G1" = 3 ] && [ "$G2" = 4 ] || restore "the placed file lacks its edits"
# ---- 10: restart, health ------------------------------------------------------------------------------------------------------------------
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for u in /finance/stock/page/amir /finance/amir /finance/sanjeevni/api/needs-you; do
  c=$(health "http://127.0.0.1:8106$u"); say "         $u $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "the gated page $u answered $c"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[10/13] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
# ---- 11-12: the proof read back ---------------------------------------------------------------------------------------------------------
say "   the owner's proof AFTER placing (the placed file, on backup-API copies of the live databases; /api/pad/hub/1 by the app's test client):"
RB="$( cd /tmp && timeout 1500 "$VPY" -B "$KDIR/state_s570.py" --finance "$FIN" --work "$WALK/state_after" 2>&1 )"
echo "$RB" | mask | cut -c1-900 | sed 's/^/   /'
echo "$RB" | grep -q "^STATE_S570 OK" || restore "the read-back of the owner's proof"
echo "$RB" | grep -q "arrived 15-10 10:11" && restore "the sentence still names the mid-day push"
say "[12/13] the owner's proof read back on the placed file (above)"
# ---- 13: nothing else moved ---------------------------------------------------------------------------------------------------------
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
md5sum "$FIN/$F" "$BAK"
rm -rf "$WALK"
say "[13/13] nothing else moved (the must-not-move files, the crontab); healthz 200 · backups: $BAK, $FIN/finance.db.bak_S570_$STAMP · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
