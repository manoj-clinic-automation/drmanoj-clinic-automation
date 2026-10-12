#!/bin/bash
# =============================================================================
#  install_S536_AMIR_BOARD_D712.sh · kit S536_AMIR_BOARD_D712 (Sanjeevni, session 310; D712 D708; F-864)
#  A small follow-up to S533: Amir's board stops printing the reception-tap arrival row (stock_app.py, stock_amir.html); the owner's
#  "live orthotic ordering can start" waits for stage C or done, dated by the first stage-C release (amir_day.py). No data step.
#
#  Run by (on the VPS, from the kit folder copied to /root/deploy/kits/S536_AMIR_BOARD_D712):  bash install_S536_AMIR_BOARD_D712.sh
#  DRY=1 : gates, build, compile, the walk on scratch copies -- nothing placed, nothing written, no lock.
#  ORDER: gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED) · the lock · gates (flask, the databases, the portal, the THREE FROM pins, the
#  spine passed and not behind the collector, the collector alive -- refused while red, charter 1b; the must-not-move md5s recorded) · build
#  (make_s536.py) · compile both pythons · scratch copies · the walk (DRY stops) · re-check · the state BEFORE · backups · place by rename ·
#  md5 read-back · the greps · ONE restart · healthz · the gated curls · the journal · the state AFTER · the read-back through a walk-only
#  portal session · nothing else moved.  /root/deploy/repo is NOT pulled (the brief: nothing in this kit needs the clone).
#  Red after placing -> the three files restored byte-identically, restart, healthz, report.
# =============================================================================
set -u
KIT="S536_AMIR_BOARD_D712"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SPN=$FIN/spine; ING=/root/marg_ingest; POR=/root/portal; AST=/root/assetapp; REPO=/root/deploy/repo
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$SPN/spine.db"
DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s536_walk_$STAMP"
SVC=clinic-finance
declare -A FROM=( [stock_app.py]=c626a46acf371b3a767756dc35743d57 [stock_amir.html]=8dd65e64aa2315da6c74909fe50c31c7
                  [amir_day.py]=262b0b814ec2b840012cd1988e420097 )
ALL=(stock_app.py stock_amir.html amir_day.py)
declare -A TO
NOTT=("$FIN/stock_watch.py" "$FIN/purchase_app.py" "$FIN/stockmatch.py" "$FIN/item_alias.py" "$FIN/stock_hub.html" "$FIN/qty_words.py"
      "$FIN/sanjeevni_approvals.py" "$FIN/aaj_seed.py" "$FIN/aaj_kaam.py" "$FIN/owner_console.py" "$FIN/amir_salts.py" "$FIN/reports_tile.py"
      "$FIN/finance_ui/finance_approvals.html" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$SPN/spine_build.py"
      "$SPN/spine_read.py" "$ING/marg_take.py")
declare -A NOTT_PIN=( ["$FIN/stock_watch.py"]=c960f6c8 ["$FIN/purchase_app.py"]=147201dd ["$FIN/stockmatch.py"]=10e30d28 )
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
state_print() {   # the state on a fresh backup-API copy of the live database, read by the files in /root/finance as they stand
  local c="$WALK/state_$1.db"; copydb "$DBF" "$c" || { say "   (no copy for the state)"; return; }
  ( cd "$FIN" && timeout 900 "$SPY" -B "$KDIR/state_s536.py" --mode state --finance "$FIN" --db "$c" 2>&1 ) | mask | cut -c1-420 | sed 's/^/   /'
  rm -f "$c"
}
bail() { say "$1"; rm -rf "$WALK"; exit "${2:-1}"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/14] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/14] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/14] PINS.sh missing - nothing done"; exit 1; }
AT=1; for f in "${ALL[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || AT=0; done
if [ "$AT" = 1 ]; then
  say "-- ALREADY INSTALLED: the three files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  state_print now; rm -rf "$WALK"; exit 0
fi
# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/14] DRY RUN: no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/14] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/14] the build lock is already held by $KIT"
else say "!! [1/14] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates --------------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || bail "!! [2/14] the venv python lacks flask (the walk); nothing placed"
"$SPY" -c "import flask" 2>/dev/null || bail "!! [2/14] the service python lacks flask; nothing placed"
for k in "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json" "$SPN/spine_state.json" "$ING/last_run.json"; do
  [ -e "$k" ] || bail "!! [2/14] $k must be reachable - nothing placed"; done
for f in "${ALL[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || bail "!! [2/14] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing placed"
done
# charter 1b: the spine passed (every gate green) and built since the collector's newest take; the collector alive (marg_ingest's last_run.json
# finished within 30 minutes -- it runs every 5) and its newest take within 72 hours (Amir comes every other day) -- S533's rule, unchanged
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
  || bail "!! [2/14] the spine is red or behind the collector (passed $SP_OK, gate $SP_GATE, last success $SP_AT, the newest take $SP_BEHIND min after it) - the kit depends on it; nothing placed (charter 1b)" 4
ING_RUN="$("$SPY" -c "
import json,sys,datetime as d
j=json.load(open(sys.argv[1])); t=d.datetime.fromisoformat(j['finished'])
print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60), int(j.get('failed') or 0))" "$ING/last_run.json" 2>/dev/null || echo "9999 0")"
ING_LOG_AGE="${ING_RUN% *}"; ING_FAILED="${ING_RUN#* }"
[ "$ING_LOG_AGE" -le 30 ] && [ "$COL_AGE" -le 72 ] || bail "!! [2/14] the collector is cold (its last run $ING_LOG_AGE min ago, newest take $COL_AGE h ago); nothing placed (charter 1b)" 4
declare -A NT0
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"; MAP0="$(m5 "$DMAP")"
say "[2/14] gates green (SUMS, KIT_ID, PINS, flask, the databases, the portal); the three files at their FROM pins; the spine passed $SP_GATE (last success $SP_AT, the newest take $SP_BEHIND min after it); the collector last ran $ING_LOG_AGE min ago ($ING_FAILED failed), its newest take $COL_AGE h ago; the clone's DUTY_MAP.json $MAP0 (read only, never pulled)"
for f in "${NOTT[@]}"; do p="${NOTT_PIN[$f]:-}"; [ -n "$p" ] && [ "${NT0[$f]:0:8}" != "$p" ] && say "   must not move: $f is ${NT0[$f]} (the brief read $p: moved before this run -- recorded; only a change DURING this install is a fault)"; done
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s536.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ALL[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || bail "!! [3/14] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing placed"; done
say "[3/14] live bytes + the anchored edits give the three pinned files"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in stock_app.py amir_day.py; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || bail "!! [4/14] compile on both pythons failed - nothing placed"
rm -rf "$WALK/cc/__pycache__"
say "[4/14] the two built python files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 5-6: scratch copies, the walk ------------------------------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance/finance_ui" "$R/$side/finance/spine" "$R/$side/marg_ingest" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance/finance_ui/"; cp -p "$SPN"/*.py "$SPN"/*.json "$R/$side/finance/spine/" 2>/dev/null
  cp -p "$ING"/*.py "$ING"/*.json "$R/$side/marg_ingest/" 2>/dev/null
  [ -f "$R/$side/finance/finance_app.py" ] && [ -f "$R/$side/marg_ingest/marg_take.py" ] || bail "!! [5/14] no scratch copy of the finance / ingest folders - nothing placed"
done
for f in "${ALL[@]}"; do cp -p "$WALK/built/$f" "$R/new/finance/$f"; done
mkdir -p "$R/por" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || bail "!! [5/14] no scratch copies - nothing placed"
say "[5/14] scratch copies: the finance and ingest folders twice (NEW with the three built files, OLD as it is), the portal's code; finance.db, assets.db and the LIVE spine.db by the backup API"
WOUT="$( cd "$R" && timeout 3600 "$VPY" -B "$KDIR/walk_s536.py" --kit "$KDIR" --work "$R/w" --run "$R" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$R/scratch_spine.db" --map "$DMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-2400 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S536 GREEN" || bail "!! [6/14] walk_s536 red - nothing placed"
say "[6/14] walk_s536 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 7-8: re-check, the state before, backups ----------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || bail "!! [7/14] the build lock is not held by $KIT - nothing placed"
for f in "${ALL[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || bail "!! [7/14] $FIN/$f moved during the walk - nothing placed"; done
say "[7/14] the lock is held by $KIT; the three FROM pins still stand after the walk"
say "   the state BEFORE placing (the old files' words, on a scratch copy of the live database):"
state_print before
declare -A BAK
for f in "${ALL[@]}"; do
  BAK[$f]="$FIN/$f.bak_S536_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || bail "!! [8/14] the backup of $f does not read back - nothing placed"
done
copydb "$DBF" "$FIN/finance.db.bak_S536_$STAMP" && [ -s "$FIN/finance.db.bak_S536_$STAMP" ] || bail "!! [8/14] database backup failed - nothing placed"
say "[8/14] three .bak_S536_<from8> beside the files; $FIN/finance.db.bak_S536_$STAMP by the backup API ($(stat -c %s "$FIN/finance.db.bak_S536_$STAMP") bytes)"
putfile() { \cp -p "$1" "$2.s536_new" && mv -f "$2.s536_new" "$2"; }
restore() {
  say "!! RED after placing ($1) - restoring the three files byte-identically"
  for f in "${ALL[@]}"; do putfile "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ALL[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC")"
  rm -rf "$WALK"; exit 1
}
# ---- 9: place, read back, the greps -------------------------------------------------------------------------------------------------------
for f in "${ALL[@]}"; do
  putfile "$WALK/built/$f" "$FIN/$f" || restore "copy $f"
  [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back $f"
done
for f in "${ALL[@]}"; do cmp -s "$FIN/$f" "$R/new/finance/$f" || restore "a placed file is not the walk's file ($f)"; done
say "[9/14] the three files placed by rename; every md5 read back = its TO pin; byte-identical to the walk's NEW copies"
G1="$(grep -c 'bill_pending' "$FIN/stock_app.py")"; G2="$(grep -c 'bill_pending' "$FIN/stock_amir.html")"; G3="$(grep -c 'bill entry baaki' "$FIN/stock_amir.html")"
say "   greps on the placed bytes: stock_app.py bill_pending $G1 · stock_amir.html bill_pending $G2, 'bill entry baaki' $G3"
[ "$G1" = 0 ] && [ "$G2" = 0 ] && [ "$G3" = 0 ] || restore "a retired name is still in a placed file"
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
say "[10/14] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
# ---- 11-12: the state after, the live read-back ---------------------------------------------------------------------------------------------
say "   the state AFTER placing (the board's section 4 as amir and the owner's lines, on a scratch copy of the live database):"
state_print after
mkdir -p "$WALK/rb_por" && for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$WALK/rb_por/"; done; cp -p "$POR/tile_grants.json" "$WALK/rb_por/"
RB="$( cd "$FIN" && FINANCE_DB="$DBF" timeout 900 "$SPY" -B "$KDIR/state_s536.py" --mode readback --finance "$FIN" --por "$WALK/rb_por" 2>&1 )"
echo "$RB" | mask | cut -c1-600 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read-back of the live board"
say "[12/14] the live board (as amir, as the owner) and Needs-you read back through a walk-only portal session"
# ---- 13-14: nothing else moved ---------------------------------------------------------------------------------------------------------
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[13/14] nothing else moved (the must-not-move files, the crontab); healthz 200; the clone's DUTY_MAP.json $(m5 "$DMAP") (was $MAP0; never pulled by this kit)"
for f in "${ALL[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "[14/14] done · healthz 200 · backups: three .bak_S536_<from8>, $FIN/finance.db.bak_S536_$STAMP · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
