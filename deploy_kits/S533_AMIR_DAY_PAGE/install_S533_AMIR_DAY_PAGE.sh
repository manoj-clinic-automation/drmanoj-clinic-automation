#!/bin/bash
# =============================================================================
#  install_S533_AMIR_DAY_PAGE.sh · kit S533_AMIR_DAY_PAGE (Sanjeevni, session 310; D706 D708 D709 D712; F-839 F-861 F-863 F-864)
#  Kit 3 of D706 -- Amir's page rebuilt once under the charter: amir_day.py replaced whole; anchored edits to stock_app.py, purchase_app.py,
#  stockmatch.py; DUTY_MAP v11 (published in the repository, pulled on the box AFTER the data step); one keyed data step.
#
#  Run by (on the VPS, from the kit folder copied to /root/deploy/kits/S533_AMIR_DAY_PAGE):  bash install_S533_AMIR_DAY_PAGE.sh
#  DRY=1 : gates, build, compile, the walk on scratch copies -- nothing placed, nothing written, no lock.
#  ORDER: gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED) · the lock · gates (flask, xlrd, the databases, the portal, the archive, the readings,
#  the FOUR FROM pins and the clone's DUTY_MAP at FROM (or already at TO), the spine passed and not behind the collector, the collector alive
#  -- refused while red, charter 1b; AMIR_BILLS_FROM in the service's environment said yes/no; the must-not-move md5s recorded) · build
#  (make_s533.py) · compile both pythons · scratch copies · the walk (DRY stops) · re-check · the state BEFORE · backups · place by rename ·
#  md5 read-back · the greps over /root/finance and /root/portal · the DATA STEP (the kit's built amir_day + purchase_app; item_alias live,
#  read-only) · ONE restart · healthz · the gated curls · the journal · the PULL of /root/deploy/repo and the DUTY_MAP TO pin · the state
#  AFTER · the read-back through a walk-only portal session · nothing else moved.
#  Red after placing -> the four files restored byte-identically, restart, healthz, report; the data step is additive (its reverse in README).
# =============================================================================
set -u
KIT="S533_AMIR_DAY_PAGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SPN=$FIN/spine; ING=/root/marg_ingest; POR=/root/portal; AST=/root/assetapp; REPO=/root/deploy/repo
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$SPN/spine.db"
BRF="$REPO/claude_code_briefs"; DMAP="$BRF/DUTY_MAP.json"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s533_walk_$STAMP"
SVC=clinic-finance
declare -A FROM=( [amir_day.py]=f90df5b211c89dc8bdcd2671e163cf94 [stock_app.py]=51620064e6849b02f0446b859a722638
                  [purchase_app.py]=c29050c18795a059e3cfbfae252efc21 [stockmatch.py]=4a2f9fcdfe969a0ca577c34536dbf9a2 )
MAP_FROM=7aa2f935677928e470454c355553210b; MD_FROM=4888a228282d37133bb888e474d2d63c
ALL=(amir_day.py stock_app.py purchase_app.py stockmatch.py)
declare -A TO
NOTT=("$FIN/item_alias.py" "$FIN/stock_amir.html" "$FIN/stock_watch.py" "$FIN/shelf_figure.py" "$FIN/reports_watch.py" "$FIN/qty_words.py" "$FIN/amir_salts.py"
      "$FIN/sanjeevni_approvals.py" "$FIN/packs.py" "$FIN/supplier_msg.py" "$FIN/scan_register.py" "$FIN/porders.py" "$FIN/returns_kinds.py" "$FIN/reports_tile.py"
      "$FIN/aaj_seed.py" "$FIN/aaj_kaam.py" "$FIN/owner_console.py" "$FIN/stock_hub.html" "$FIN/stock_statement.py" "$FIN/finance_ui/finance_approvals.html"
      "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$SPN/spine_build.py" "$SPN/marg_read.py" "$SPN/spine_read.py" "$ING/marg_take.py")
declare -A NOTT_PIN=( ["$FIN/item_alias.py"]=111a8e48 ["$FIN/stock_amir.html"]=8dd65e64 ["$FIN/stock_watch.py"]=c960f6c8 ["$FIN/qty_words.py"]=706db7cc
                      ["$FIN/sanjeevni_approvals.py"]=792f4a9a ["$FIN/stock_hub.html"]=a710a98a ["$FIN/finance_ui/finance_approvals.html"]=b32da7ff )
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
  ( cd "$FIN" && timeout 900 "$SPY" -B "$KDIR/state_s533.py" --mode state --finance "$FIN" --db "$c" 2>&1 ) | mask | cut -c1-420 | sed 's/^/   /'
  rm -f "$c"
}
bail() { say "$1"; rm -rf "$WALK"; exit "${2:-1}"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/16] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/16] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/16] PINS.sh missing - nothing done"; exit 1; }
[ "$(m5 "$KDIR/amir_day.py")" = "${TO[amir_day.py]}" ] || { say "!! [0/16] the kit's amir_day.py is not at its TO pin - nothing done"; exit 1; }
AT=1; for f in "${ALL[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || AT=0; done
if [ "$AT" = 1 ]; then
  say "-- ALREADY INSTALLED: the four files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz); DUTY_MAP.json $(m5 "$DMAP")"
  state_print now; rm -rf "$WALK"; exit 0
fi
# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/16] DRY RUN: no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/16] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/16] the build lock is already held by $KIT"
else say "!! [1/16] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates --------------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || bail "!! [2/16] the venv python lacks flask (the walk); nothing placed"
"$SPY" -c "import flask, xlrd" 2>/dev/null || bail "!! [2/16] the service python lacks flask or xlrd (the data step reads the closing .xls as marg_take does); nothing placed"
for k in "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json" "$DMAP" "$BRF/DUTY_MAP.md" "$SPN/spine_state.json" "$ING/archive" "$SPN/readings"; do
  [ -e "$k" ] || bail "!! [2/16] $k must be reachable - nothing placed"; done
for f in "${ALL[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || bail "!! [2/16] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing placed"
done
MAP0="$(m5 "$DMAP")"; MD0="$(m5 "$BRF/DUTY_MAP.md")"
{ [ "$MAP0" = "$MAP_FROM" ] && [ "$MD0" = "$MD_FROM" ]; } || { [ "$MAP0" = "${TO[DUTY_MAP.json]}" ] && [ "$MD0" = "${TO[DUTY_MAP.md]}" ]; } \
  || bail "!! [2/16] the clone's DUTY_MAP.json/.md are $MAP0/$MD0 -- neither the FROM pins nor the kit's TO pins; nothing placed"
# charter 1b: the spine passed (every gate green) and built since the collector's newest take (the cron builds within 10 minutes); the collector
# alive (marg_ingest's last_run.json finished within 30 minutes -- it runs every 5) and its newest take within 72 hours (Amir comes every other day)
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
ENVHAS="$(systemctl show "$SVC" -p Environment 2>/dev/null | grep -c 'AMIR_BILLS_FROM' || true)"
declare -A NT0
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/16] gates green (SUMS, KIT_ID, PINS, flask, xlrd, the databases, the portal, the archive, the readings); the four files at their FROM pins; the clone's DUTY_MAP $([ "$MAP0" = "$MAP_FROM" ] && echo 'at v10 FROM' || echo 'already at the kit TO'); the spine passed $SP_GATE (last success $SP_AT, the newest take $SP_BEHIND min after it); the collector last ran $ING_LOG_AGE min ago ($ING_FAILED failed), its newest take $COL_AGE h ago; AMIR_BILLS_FROM in $SVC's environment: $([ "$ENVHAS" = 0 ] && echo no || echo yes)"
for f in "${NOTT[@]}"; do p="${NOTT_PIN[$f]:-}"; [ -n "$p" ] && [ "${NT0[$f]:0:8}" != "$p" ] && say "   must not move: $f is ${NT0[$f]} (the brief read $p: moved before this run -- recorded; only a change DURING this install is a fault)"; done
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" "$WALK/mods" || exit 1
"$SPY" -B make_s533.py --finance "$FIN" --briefs "$BRF" --out "$WALK/built" | sed 's/^/   /'
for f in "${ALL[@]}" DUTY_MAP.json DUTY_MAP.md; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || bail "!! [3/16] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing placed"; done
cp -p "$WALK/built/amir_day.py" "$WALK/built/purchase_app.py" "$WALK/mods/"
say "[3/16] live bytes + the anchored edits give the three pinned python files; amir_day.py is the kit's whole file; DUTY_MAP v11 built from the clone"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ALL[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || bail "!! [4/16] compile on both pythons failed - nothing placed"
rm -rf "$WALK/cc/__pycache__"
say "[4/16] the four built files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
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
say "[5/16] scratch copies: the finance and ingest folders twice (NEW with the four built files, OLD as it is), the portal's code; finance.db, assets.db and the LIVE spine.db by the backup API"
WOUT="$( cd "$R" && timeout 5400 "$VPY" -B "$KDIR/walk_s533.py" --kit "$KDIR" --work "$R/w" --run "$R" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$R/scratch_spine.db" --built "$WALK/mods" --map-new "$WALK/built/DUTY_MAP.json" --map-old "$DMAP" --archive "$ING/archive" --readings "$SPN/readings" 2>&1 )"
echo "$WOUT" | mask | cut -c1-2400 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S533 GREEN" || bail "!! [6/16] walk_s533 red - nothing placed"
say "[6/16] walk_s533 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 7-8: re-check, the state before, backups ----------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || bail "!! [7/16] the build lock is not held by $KIT - nothing placed"
for f in "${ALL[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || bail "!! [7/16] $FIN/$f moved during the walk - nothing placed"; done
say "[7/16] the lock is held by $KIT; the four FROM pins still stand after the walk"
say "   the state BEFORE placing (the old files' words, on a scratch copy of the live database):"
state_print before
declare -A BAK
for f in "${ALL[@]}"; do
  BAK[$f]="$FIN/$f.bak_S533_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || bail "!! [8/16] the backup of $f does not read back - nothing placed"
done
copydb "$DBF" "$FIN/finance.db.bak_S533_$STAMP" && [ -s "$FIN/finance.db.bak_S533_$STAMP" ] || bail "!! [8/16] database backup failed - nothing placed"
say "[8/16] four .bak_S533_<from8> beside the files; $FIN/finance.db.bak_S533_$STAMP by the backup API ($(stat -c %s "$FIN/finance.db.bak_S533_$STAMP") bytes)"
putfile() { \cp -p "$1" "$2.s533_new" && mv -f "$2.s533_new" "$2"; }
restore() {
  say "!! RED after placing ($1) - restoring the four files byte-identically (the data step is additive: new tables and columns stay, unread by the old files; its reverse is in README.md)"
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
say "[9/16] the four files placed by rename; every md5 read back = its TO pin; byte-identical to the walk's NEW copies"
G="$( "$SPY" -B "$KDIR/state_s533.py" --mode grep --dirs "$FIN" "$POR" 2>&1 )"; GRC=$?
echo "$G" | mask | cut -c1-300 | sed 's/^/   /'
[ "$GRC" = 0 ] || restore "a retired name is still read somewhere"
# ---- 10: the data step (the kit's built amir_day + purchase_app, copied out of the kit folder) ------------------------------------------------
DOUT="$( cd "$FIN" && timeout 900 "$SPY" -B "$KDIR/data_s533.py" --db "$DBF" --modules "$WALK/mods" --finance "$FIN" --archive "$ING/archive" --readings "$SPN/readings" 2>&1 )"; DRC=$?
echo "$DOUT" | mask | cut -c1-330 | sed 's/^/   /'
[ "$DRC" = 0 ] && echo "$DOUT" | grep -q "^DATA_S533: committed" || restore "the data step did not run clean (exit $DRC)"
say "[10/16] the data step ran on the live database (above)"
# ---- 11: restart, health ------------------------------------------------------------------------------------------------------------------
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for u in /finance/amir /finance/amir/step/5 /finance/amir/day; do
  c=$(health "http://127.0.0.1:8106$u"); say "         $u $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "the gated page $u answered $c"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[11/16] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
# ---- 12: the pull -- the duty map v11 only now that its tables exist (R3-8) -------------------------------------------------------------------
PULL="$(git -C "$REPO" pull --ff-only 2>&1)"; PRC=$?
echo "$PULL" | tail -3 | sed 's/^/   /'
MAP1="$(m5 "$DMAP")"; MD1="$(m5 "$BRF/DUTY_MAP.md")"
if [ "$MAP1" = "${TO[DUTY_MAP.json]}" ] && [ "$MD1" = "${TO[DUTY_MAP.md]}" ]; then
  say "[12/16] $REPO pulled; claude_code_briefs/DUTY_MAP.json is v11 at its TO pin $MAP1; DUTY_MAP.md $MD1"
  ( cd "$REPO/deploy_kits/$KIT" 2>/dev/null && md5sum -c SUMS.md5 >/dev/null 2>&1 ) && say "   the repository's kit folder is byte-identical to the one that ran (SUMS.md5)" \
    || say "   !! the repository's kit folder does not match SUMS.md5 -- said for the report"
else
  say "!! [12/16] the pull did not bring DUTY_MAP v11 (exit $PRC; DUTY_MAP.json $MAP1) -- the map stays v10: valid against the old tables, stale; said for the report"
fi
# ---- 13-14: the state after, the live read-back ---------------------------------------------------------------------------------------------
say "   the state AFTER placing (the words Amir and the owner see, on a scratch copy of the live database):"
state_print after
mkdir -p "$WALK/rb_por" && for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$WALK/rb_por/"; done; cp -p "$POR/tile_grants.json" "$WALK/rb_por/"
RB="$( cd "$FIN" && FINANCE_DB="$DBF" timeout 900 "$SPY" -B "$KDIR/state_s533.py" --mode readback --finance "$FIN" --por "$WALK/rb_por" 2>&1 )"
echo "$RB" | mask | cut -c1-600 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read-back of the live pages"
say "[14/16] the live pages read back through a walk-only portal session (the owner's day, the visit summary, Needs-you; Amir's steps 1, 6, 7)"
# ---- 15-16: nothing else moved ---------------------------------------------------------------------------------------------------------
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[15/16] nothing else moved (the must-not-move files, the crontab); healthz 200"
for f in "${ALL[@]}"; do md5sum "$FIN/$f"; done
md5sum "$DMAP" "$BRF/DUTY_MAP.md"
rm -rf "$WALK"
say "[16/16] done · healthz 200 · backups: four .bak_S533_<from8>, $FIN/finance.db.bak_S533_$STAMP · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
