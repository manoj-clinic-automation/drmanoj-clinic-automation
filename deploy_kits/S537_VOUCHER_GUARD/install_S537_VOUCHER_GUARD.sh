#!/bin/bash
# =============================================================================
#  install_S537_VOUCHER_GUARD.sh · kit S537_VOUCHER_GUARD (Sanjeevni, session 310; the owner's "Yes" of 12-Oct 07:02 IST; F-185)
#  Voucher 29 voided; a voucher line that would take Marg below zero (by the item's full name on Marg's newest closing) never goes to Amir;
#  a settled item is never raised again; an arrival tied to its bill is never "bill missing". Anchored edits to stock_app.py, stock_watch.py,
#  shelf_figure.py, stock_statement.py, loss_piles.py; DUTY_MAP v12 (published in the repository, pulled AFTER the tables exist); one keyed
#  data step.
#
#  Run by (on the VPS, from the kit folder copied to /root/deploy/kits/S537_VOUCHER_GUARD):  bash install_S537_VOUCHER_GUARD.sh
#  DRY=1 : gates, build, compile, the walk on scratch copies -- nothing placed, nothing written, no lock.
#  ORDER (the brief's section 5): gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED) · the lock · gates (flask, the databases, the portal, the FIVE
#  FROM pins and the clone's DUTY_MAP at v11, the spine passed and not behind the collector, the collector alive -- refused while red, charter
#  1b; the must-not-move md5s recorded) · build (make_s537.py) · compile both pythons · scratch copies · the walk (DRY stops) · re-check · the
#  state BEFORE · backups · place by rename · md5 read-back · the greps · data_s537.py --schema-only · the PULL of /root/deploy/repo and the
#  DUTY_MAP v12 gate (not v12 -> no void: the files restored, report) · data_s537.py (a STOP restores the files) · ONE restart · healthz · the
#  gated curls · the journal · the state AFTER · the read-back through a walk-only portal session · nothing else moved.
#  Red after placing -> the five files restored byte-identically, restart, healthz, report. The two tables are additive (the old files never
#  read them); the database backup is kept.
# =============================================================================
set -u
KIT="S537_VOUCHER_GUARD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SPN=$FIN/spine; ING=/root/marg_ingest; POR=/root/portal; AST=/root/assetapp; REPO=/root/deploy/repo
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$SPN/spine.db"
BRF="$REPO/claude_code_briefs"; DMAP="$BRF/DUTY_MAP.json"; DMD="$BRF/DUTY_MAP.md"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s537_walk_$STAMP"
SVC=clinic-finance
declare -A FROM=( [stock_app.py]=8d55637c3ab59a323cff1a0efb021527 [stock_watch.py]=c960f6c890e3e83c58b88d8a7f219752
                  [shelf_figure.py]=9be5eb88d1b1fc1fdb03b906c88a4265 [stock_statement.py]=1a4f6c9ecb2546dae954c0414074f406
                  [loss_piles.py]=202bfc4e3fd798501c6db95373c2a7d4 )
MAP_FROM=69b8f56b17da263b932426b87a7abc1c; MD_FROM=553398f3a21541e688d3f3c72e585748
ALL=(stock_app.py stock_watch.py shelf_figure.py stock_statement.py loss_piles.py)
declare -A TO
NOTT=("$FIN/amir_day.py" "$FIN/stock_amir.html" "$FIN/stockmatch.py" "$FIN/item_alias.py" "$FIN/porders.py" "$FIN/purchase_app.py" "$FIN/qty_words.py"
      "$FIN/aaj_seed.py" "$FIN/aaj_kaam.py" "$FIN/owner_console.py" "$FIN/stock_hub.html" "$FIN/sanjeevni_approvals.py" "$FIN/reports_tile.py"
      "$FIN/finance_ui/finance_approvals.html" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$SPN/spine_build.py"
      "$SPN/spine_read.py" "$ING/marg_take.py")
declare -A NOTT_PIN=( ["$FIN/amir_day.py"]=73882a83 ["$FIN/stock_amir.html"]=72034c2e ["$FIN/stockmatch.py"]=10e30d28 ["$FIN/item_alias.py"]=111a8e48
                      ["$FIN/porders.py"]=a5a823bf ["$FIN/aaj_seed.py"]=156ded1e ["$FIN/aaj_kaam.py"]=cd232b1c ["$FIN/owner_console.py"]=c09321e2 )
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
  ( cd "$FIN" && timeout 900 "$SPY" -B "$KDIR/state_s537.py" --mode state --finance "$FIN" --db "$c" 2>&1 ) | mask | cut -c1-640 | sed 's/^/   /'
  rm -f "$c"
}
bail() { say "$1"; rm -rf "$WALK"; exit "${2:-1}"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/16] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/16] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/16] PINS.sh missing - nothing done"; exit 1; }
AT=1; for f in "${ALL[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || AT=0; done
if [ "$AT" = 1 ]; then
  say "-- ALREADY INSTALLED: the five files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz); DUTY_MAP.json $(m5 "$DMAP")"
  state_print now; rm -rf "$WALK"; exit 0
fi
# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/16] DRY RUN: no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/16] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/16] the build lock is already held by $KIT"
else say "!! [1/16] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates --------------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || bail "!! [2/16] the venv python lacks flask (the walk); nothing placed"
"$SPY" -c "import flask" 2>/dev/null || bail "!! [2/16] the service python lacks flask; nothing placed"
for k in "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json" "$DMAP" "$DMD" "$SPN/spine_state.json" "$ING/last_run.json"; do
  [ -e "$k" ] || bail "!! [2/16] $k must be reachable - nothing placed"; done
for f in "${ALL[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || bail "!! [2/16] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing placed"
done
MAP0="$(m5 "$DMAP")"; MD0="$(m5 "$DMD")"
[ "$MAP0" = "$MAP_FROM" ] && [ "$MD0" = "$MD_FROM" ] || bail "!! [2/16] the clone's DUTY_MAP.json/.md are $MAP0/$MD0, not v11's FROM pins $MAP_FROM/$MD_FROM (the map must go live only after the tables exist); nothing placed"
# charter 1b: the spine passed (every gate green) and built since the collector's newest take; the collector alive (marg_ingest's last_run.json
# finished within 30 minutes -- it runs every 5) and its newest take within 72 hours -- S533 / S536's rule, unchanged
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
  || bail "!! [2/16] the spine is red or behind the collector (passed $SP_OK, gate $SP_GATE, last success $SP_AT, the newest take $SP_BEHIND min after it) - the kit depends on it; nothing placed (charter 1b)" 4
ING_RUN="$("$SPY" -c "
import json,sys,datetime as d
j=json.load(open(sys.argv[1])); t=d.datetime.fromisoformat(j['finished'])
print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60), int(j.get('failed') or 0))" "$ING/last_run.json" 2>/dev/null || echo "9999 0")"
ING_LOG_AGE="${ING_RUN% *}"; ING_FAILED="${ING_RUN#* }"
[ "$ING_LOG_AGE" -le 30 ] && [ "$COL_AGE" -le 72 ] || bail "!! [2/16] the collector is cold (its last run $ING_LOG_AGE min ago, newest take $COL_AGE h ago); nothing placed (charter 1b)" 4
declare -A NT0
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/16] gates green (SUMS, KIT_ID, PINS, flask, the databases, the portal); the five files at their FROM pins; the clone's DUTY_MAP at v11 FROM; the spine passed $SP_GATE (last success $SP_AT, the newest take $SP_BEHIND min after it); the collector last ran $ING_LOG_AGE min ago ($ING_FAILED failed), its newest take $COL_AGE h ago"
for f in "${NOTT[@]}"; do p="${NOTT_PIN[$f]:-}"; [ -n "$p" ] && [ "${NT0[$f]:0:8}" != "$p" ] && say "   must not move: $f is ${NT0[$f]} (the brief read $p: moved before this run -- recorded; only a change DURING this install is a fault)"; done
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s537.py --finance "$FIN" --briefs "$BRF" --out "$WALK/built" | sed 's/^/   /'
for f in "${ALL[@]}" DUTY_MAP.json DUTY_MAP.md; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || bail "!! [3/16] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing placed"; done
say "[3/16] live bytes + the anchored edits give the five pinned python files; DUTY_MAP v12 built from the clone at its TO pins"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ALL[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || bail "!! [4/16] compile on both pythons failed - nothing placed"
rm -rf "$WALK/cc/__pycache__"
say "[4/16] the five built files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 5-6: scratch copies, the walk ------------------------------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance/finance_ui" "$R/$side/finance/spine" "$R/$side/marg_ingest" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance/finance_ui/"; cp -p "$SPN"/*.py "$SPN"/*.json "$R/$side/finance/spine/" 2>/dev/null
  cp -p "$ING"/*.py "$ING"/*.json "$R/$side/marg_ingest/" 2>/dev/null
  [ -f "$R/$side/finance/finance_app.py" ] && [ -f "$R/$side/marg_ingest/marg_take.py" ] || bail "!! [5/16] no scratch copy of the finance / ingest folders - nothing placed"
done
for f in "${ALL[@]}"; do cp -p "$WALK/built/$f" "$R/new/finance/$f"; done
mkdir -p "$R/por" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || bail "!! [5/16] no scratch copies - nothing placed"
say "[5/16] scratch copies: the finance and ingest folders twice (NEW with the five built files, OLD as it is), the portal's code; finance.db, assets.db and the LIVE spine.db by the backup API"
WOUT="$( cd "$R" && timeout 5400 "$VPY" -B "$KDIR/walk_s537.py" --kit "$KDIR" --work "$R/w" --run "$R" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$R/scratch_spine.db" --map-old "$DMAP" --map-new "$WALK/built/DUTY_MAP.json" 2>&1 )"
echo "$WOUT" | mask | cut -c1-2400 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S537 GREEN" || bail "!! [6/16] walk_s537 red - nothing placed"
say "[6/16] walk_s537 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 7-8: re-check, the state before, backups ----------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || bail "!! [7/16] the build lock is not held by $KIT - nothing placed"
for f in "${ALL[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || bail "!! [7/16] $FIN/$f moved during the walk - nothing placed"; done
[ "$(m5 "$DMAP")" = "$MAP_FROM" ] || bail "!! [7/16] the clone's DUTY_MAP.json moved during the walk - nothing placed"
say "[7/16] the lock is held by $KIT; the five FROM pins and the clone's v11 map still stand after the walk"
say "   the state BEFORE placing (the old files' words, on a scratch copy of the live database):"
state_print before
declare -A BAK
for f in "${ALL[@]}"; do
  BAK[$f]="$FIN/$f.bak_S537_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || bail "!! [8/16] the backup of $f does not read back - nothing placed"
done
copydb "$DBF" "$FIN/finance.db.bak_S537_$STAMP" && [ -s "$FIN/finance.db.bak_S537_$STAMP" ] || bail "!! [8/16] database backup failed - nothing placed"
say "[8/16] five .bak_S537_<from8> beside the files; $FIN/finance.db.bak_S537_$STAMP by the backup API ($(stat -c %s "$FIN/finance.db.bak_S537_$STAMP") bytes)"
putfile() { \cp -p "$1" "$2.s537_new" && mv -f "$2.s537_new" "$2"; }
restore() {
  say "!! RED after placing ($1) - restoring the five files byte-identically (the two new tables stay: additive, the old files never read them; the database backup is kept)"
  for f in "${ALL[@]}"; do putfile "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ALL[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the clone's DUTY_MAP.json $(m5 "$DMAP")"
  rm -rf "$WALK"; exit 1
}
# ---- 9: place, read back, the greps -------------------------------------------------------------------------------------------------------
for f in "${ALL[@]}"; do
  putfile "$WALK/built/$f" "$FIN/$f" || restore "copy $f"
  [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back $f"
done
for f in "${ALL[@]}"; do cmp -s "$FIN/$f" "$R/new/finance/$f" || restore "a placed file is not the walk's file ($f)"; done
say "[9/16] the five files placed by rename; every md5 read back = its TO pin; byte-identical to the walk's NEW copies"
G1="$(grep -c '_void_sql(' "$FIN/stock_app.py")"; G2="$(grep -c '_void_sql(' "$FIN/shelf_figure.py")"; G3="$(grep -c '_void_sql(' "$FIN/stock_statement.py")"
G4="$(grep -c "COALESCE(l.billed_bill_no,'') = ''" "$FIN/stock_watch.py")"; G6="$(grep -c '_voucher_lines(' "$FIN/loss_piles.py")"
say "   greps on the placed bytes: stock_app _void_sql( $G1 (the def + seven readers) · shelf_figure $G2 · stock_statement $G3 · stock_watch billed_bill_no test $G4 · loss_piles _voucher_lines( $G6"
[ "$G1" = 8 ] && [ "$G2" = 1 ] && [ "$G3" = 1 ] && [ "$G4" = 1 ] && [ "$G6" = 1 ] || restore "a placed file lacks its edit"
# ---- 10: the tables, then the map, then the rows (the brief's 2.6 order) ------------------------------------------------------------------
SOUT="$( cd "$FIN" && timeout 600 "$SPY" -B "$KDIR/data_s537.py" --db "$DBF" --finance "$FIN" --schema-only 2>&1 )"; SRC=$?
echo "$SOUT" | mask | cut -c1-300 | sed 's/^/   /'
[ "$SRC" = 0 ] && echo "$SOUT" | grep -q "^DATA_S537: schema committed" || restore "the schema step did not run clean (exit $SRC)"
say "[10/16] stock_voucher_void and stock_voucher_settle laid on the live database (stock_app._voucher_ensure)"
PULL="$(git -C "$REPO" pull --ff-only 2>&1)"; PRC=$?
echo "$PULL" | tail -3 | sed 's/^/   /'
MAP1="$(m5 "$DMAP")"; MD1="$(m5 "$DMD")"
if [ "$MAP1" = "${TO[DUTY_MAP.json]}" ] && [ "$MD1" = "${TO[DUTY_MAP.md]}" ]; then
  say "[11/16] $REPO pulled; claude_code_briefs/DUTY_MAP.json is v12 at its TO pin $MAP1; DUTY_MAP.md $MD1"
  ( cd "$REPO/deploy_kits/$KIT" 2>/dev/null && md5sum -c SUMS.md5 >/dev/null 2>&1 ) && say "   the repository's kit folder is byte-identical to the one that ran (SUMS.md5)" \
    || say "   !! the repository's kit folder does not match SUMS.md5 -- said for the report"
else
  restore "the pull did not bring DUTY_MAP v12 (exit $PRC; DUTY_MAP.json $MAP1, .md $MD1) -- no void written (a void with the v11 map would leave Amir's list counting a voucher his board no longer shows)"
fi
DOUT="$( cd "$FIN" && timeout 1800 "$SPY" -B "$KDIR/data_s537.py" --db "$DBF" --finance "$FIN" 2>&1 )"; DRC=$?
echo "$DOUT" | mask | cut -c1-400 | sed 's/^/   /'
[ "$DRC" = 0 ] && echo "$DOUT" | grep -q "^DATA_S537: committed" || restore "the data step did not run clean (exit $DRC)"
say "[12/16] the data step ran on the live database (above)"
# ---- 13: restart, health ------------------------------------------------------------------------------------------------------------------
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
say "[13/16] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
# ---- 14-15: the state after, the live read-back ---------------------------------------------------------------------------------------------
say "   the state AFTER placing (the words Amir and the owner see, on a scratch copy of the live database):"
state_print after
mkdir -p "$WALK/rb_por" && for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$WALK/rb_por/"; done; cp -p "$POR/tile_grants.json" "$WALK/rb_por/"
RB="$( cd "$FIN" && FINANCE_DB="$DBF" timeout 900 "$SPY" -B "$KDIR/state_s537.py" --mode readback --finance "$FIN" --por "$WALK/rb_por" 2>&1 )"
echo "$RB" | mask | cut -c1-600 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read-back of the live board"
say "[15/16] the live board (as amir, as the owner) and Needs-you read back through a walk-only portal session"
# ---- 16: nothing else moved ---------------------------------------------------------------------------------------------------------
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "   nothing else moved (the must-not-move files, the crontab); healthz 200"
for f in "${ALL[@]}"; do md5sum "$FIN/$f"; done
md5sum "$DMAP" "$DMD"
rm -rf "$WALK"
say "[16/16] done · healthz 200 · backups: five .bak_S537_<from8>, $FIN/finance.db.bak_S537_$STAMP · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
