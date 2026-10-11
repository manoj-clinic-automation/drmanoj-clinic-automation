#!/bin/bash
# =============================================================================
#  install_S528_AMIR_PAGE.sh · kit S528_AMIR_PAGE (Sanjeevni, session 308, 11-Oct-2026; D706 D708 D709; F-851 F-852 F-853 F-854)
#  Kit 2 of three on Amir's page: the judgment reaches the screens rightly, and the renames by identity. Four live files:
#  stock_app.py, item_alias.py, amir_day.py (anchored edits) and stock_amir.html (replaced whole); one additive data step.
#
#  Run by (on the VPS):   bash <kit>/install_S528_AMIR_PAGE.sh        DRY=1 : gates, build, compile, walk on scratch copies only.
#  ORDER: gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED) · the lock · gates (flask in the venv, flask+xlrd in the service python, the databases, the portal, the FOUR FROM pins,
#  the spine's spine_state.json passed and fresh, the collector alive -- refused while red, charter 1b; the must-not-move md5s recorded) · build
#  (make_s528.py) · compile both pythons · scratch copies (finance + ingest twice, the portal's code, finance.db / assets.db / the LIVE spine.db by
#  the backup API) · the walk (DRY stops) · re-check · the state BEFORE · backups (.bak_S528_<from8> beside each file, finance.db.bak_S528) ·
#  place by rename · md5 read-back · the greps over /root/finance and /root/portal · the DATA STEP (the kit's item_alias on the live database) ·
#  ONE restart · healthz · the gated curls · the journal · the state AFTER · the read-back of the live board · nothing else moved.
#  Red after placing -> the four files restored byte-identically, restart, healthz, report; the data step is additive (its reverse is in README.md).
# =============================================================================
set -u
KIT="S528_AMIR_PAGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; SPN=$FIN/spine; ING=/root/marg_ingest; POR=/root/portal; AST=/root/assetapp
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$SPN/spine.db"
DMAP="${DUTY_MAP_PATH:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s528_walk_$STAMP"
SVC=clinic-finance
declare -A FROM=( [stock_app.py]=b7e9880af7b81d38e7760b98d0a262b5 [item_alias.py]=5168c3c05df63a674a8dcab59f74365f [amir_day.py]=7f9803d813b59df287e9175de06f6d36
                  [stock_amir.html]=2e41e406e3b2ef9d7ed75f9f24b923b8 )
ALL=(stock_app.py item_alias.py amir_day.py stock_amir.html)
BUILT=(stock_app.py item_alias.py amir_day.py)
declare -A TO
NOTT=("$FIN/stockmatch.py" "$FIN/shelf_figure.py" "$FIN/stock_watch.py" "$FIN/reports_watch.py" "$FIN/qty_words.py" "$FIN/purchase_app.py" "$FIN/amir_salts.py"
      "$FIN/sanjeevni_approvals.py" "$FIN/stock_hub.html" "$FIN/stock_report.html" "$FIN/stock_desk.html" "$FIN/finance_ui/finance_approvals.html" "$ING/marg_take.py"
      "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$SPN/spine_build.py" "$SPN/marg_read.py" "$SPN/spine_read.py" "$DMAP")
declare -A NOTT_PIN=( ["$FIN/stockmatch.py"]=4a2f9fcd ["$FIN/shelf_figure.py"]=9be5eb88 ["$FIN/stock_watch.py"]=c960f6c8 ["$FIN/reports_watch.py"]=a8bbd95e ["$FIN/qty_words.py"]=706db7cc
                      ["$FIN/purchase_app.py"]=c29050c1 ["$FIN/sanjeevni_approvals.py"]=792f4a9a ["$FIN/stock_hub.html"]=a710a98a ["$FIN/finance_ui/finance_approvals.html"]=b32da7ff
                      ["$ING/marg_take.py"]=5cad2d24 ["$DMAP"]=7aa2f935 )
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
state_print() { ( cd "$FIN" && FINANCE_DB="$DBF" timeout 600 "$SPY" -B "$KDIR/state_s528.py" --finance "$FIN" --mode state 2>&1 ) | mask | cut -c1-400 | sed 's/^/   /'; }
bail() { say "$1"; rm -rf "$WALK"; exit "${2:-1}"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/15] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/15] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/15] PINS.sh missing - nothing done"; exit 1; }
AT=1; for f in "${ALL[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || AT=0; done
if [ "$AT" = 1 ]; then
  say "-- ALREADY INSTALLED: the four files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  state_print; rm -rf "$WALK"; exit 0
fi
# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/15] DRY RUN: no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/15] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/15] the build lock is already held by $KIT"
else say "!! [1/15] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates --------------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || bail "!! [2/15] the venv python lacks flask (the walk); nothing placed"
"$SPY" -c "import flask, xlrd" 2>/dev/null || bail "!! [2/15] the service python lacks flask or xlrd (the data step reads the closing .xls as marg_take does); nothing placed"
for k in "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json" "$DMAP" "$SPN/spine_state.json" "$ING/archive" "$SPN/readings"; do
  [ -e "$k" ] || bail "!! [2/15] $k must be reachable - nothing placed"; done
for f in "${ALL[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || bail "!! [2/15] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing placed"
done
# charter 1b: the spine passed and fresh (built within 2 hours), the collector alive (an export taken within 24 hours)
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$SPY" -c "import datetime as d,sys; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 99999)"
[ "$SP_OK" = True ] && [ "$SP_GATE" = "13/13" ] && [ "$SP_AGE" -le 120 ] || bail "!! [2/15] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - the kit depends on it; nothing placed (charter 1b)" 4
COL_AGE="$("$SPY" -c "
import sqlite3,sys,datetime as d
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
r=c.execute(\"SELECT MAX(received_at) FROM mi_file\").fetchone()[0]
t=d.datetime.fromisoformat(r); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//3600))" "$DBF" 2>/dev/null || echo 9999)"
[ "$COL_AGE" -le 24 ] || bail "!! [2/15] the collector took no export in the last 24 hours ($COL_AGE h) - the renames' door is cold; nothing placed (charter 1b)" 4
declare -A NT0
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/15] gates green (SUMS, KIT_ID, PINS, flask, xlrd, the databases, the portal, the archive, the readings); the four files at their FROM pins; the spine passed $SP_GATE ($SP_AGE min ago); the collector's newest export $COL_AGE h ago"
for f in "${NOTT[@]}"; do p="${NOTT_PIN[$f]:-}"; [ -n "$p" ] && [ "${NT0[$f]:0:8}" != "$p" ] && say "   must not move: $f is ${NT0[$f]} (the brief read $p: moved before this run -- recorded; only a change DURING this install is a fault)"; done
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s528.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${BUILT[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || bail "!! [3/15] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing placed"; done
cp -p "$KDIR/stock_amir.html" "$WALK/built/stock_amir.html"
[ "$(m5 "$WALK/built/stock_amir.html")" = "${TO[stock_amir.html]}" ] || bail "!! [3/15] the kit's stock_amir.html is not at its pin - nothing placed"
say "[3/15] live bytes + the anchored edits give the three pinned python files; stock_amir.html is the kit's whole file at its pin"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${BUILT[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || bail "!! [4/15] compile on both pythons failed - nothing placed"
rm -rf "$WALK/cc/__pycache__"
say "[4/15] the three built files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 5-6: scratch copies, the walk ------------------------------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance/finance_ui" "$R/$side/finance/spine" "$R/$side/marg_ingest" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance/finance_ui/"; cp -p "$SPN"/*.py "$SPN"/*.json "$R/$side/finance/spine/" 2>/dev/null
  cp -p "$ING"/*.py "$ING"/*.json "$R/$side/marg_ingest/" 2>/dev/null
  [ -f "$R/$side/finance/finance_app.py" ] && [ -f "$R/$side/marg_ingest/marg_take.py" ] || bail "!! [5/15] no scratch copy of the finance / ingest folders - nothing placed"
done
for f in "${ALL[@]}"; do cp -p "$WALK/built/$f" "$R/new/finance/$f"; done
mkdir -p "$R/por" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || bail "!! [5/15] no scratch copies - nothing placed"
say "[5/15] scratch copies: the finance and ingest folders twice (NEW with the four built files, OLD as it is), the portal's code; finance.db, assets.db and the LIVE spine.db by the backup API"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s528.py" --kit "$KDIR" --work "$R/w" --run "$R" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$R/scratch_spine.db" --duty-map "$DMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-2200 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S528 GREEN" || bail "!! [6/15] walk_s528 red - nothing placed"
say "[6/15] walk_s528 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 7-8: re-check, the state before, backups ----------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || bail "!! [7/15] the build lock is not held by $KIT - nothing placed"
for f in "${ALL[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || bail "!! [7/15] $FIN/$f moved during the walk - nothing placed"; done
say "[7/15] the lock is held by $KIT; the four FROM pins still stand after the walk"
say "   the state BEFORE placing (the old file's words):"
state_print
declare -A BAK
for f in "${ALL[@]}"; do
  BAK[$f]="$FIN/$f.bak_S528_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || bail "!! [8/15] the backup of $f does not read back - nothing placed"
done
copydb "$DBF" "$FIN/finance.db.bak_S528_$STAMP" && [ -s "$FIN/finance.db.bak_S528_$STAMP" ] || bail "!! [8/15] database backup failed - nothing placed"
say "[8/15] four .bak_S528_<from8> beside the files; $FIN/finance.db.bak_S528_$STAMP by the backup API ($(stat -c %s "$FIN/finance.db.bak_S528_$STAMP") bytes)"
putfile() { \cp -p "$1" "$2.s528_new" && mv -f "$2.s528_new" "$2"; }
restore() {
  say "!! RED after placing ($1) - restoring the four files byte-identically (the data step is additive; its reverse is in README.md)"
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
say "[9/15] the four files placed by rename; every md5 read back = its TO pin; byte-identical to the walk's NEW copies"
G="$(grep -rn -E '(^|[^A-Za-z0-9_])(_s436_board_extra|_s452_board_roman|_s446_board_filter|_s521_stage_proof|_s521_wrong_hi|_s521_export_hi|S521_EXPORT_HI|S452_REASONS_ROMAN|_s446_wrong_lines)($|[^A-Za-z0-9_])|(^|[^A-Za-z0-9_])_amir_board\(' "$FIN" "$POR" --include=*.py --include=*.html 2>/dev/null | grep -v '\.bak_' | grep -v '/pad_uploads/' | head -5)"
G2="$(grep -rn -E '(^|[^A-Za-z0-9_])(S488_TAIL_HI|_s488_tail_hi)($|[^A-Za-z0-9_])' "$FIN" "$POR" --include=*.py --include=*.html 2>/dev/null | grep -v '\.bak_' | grep -v "$FIN/amir_day.py" | head -5)"
[ -z "$G$G2" ] || restore "a retired name is still read somewhere: $G $G2"
say "   greps over $FIN and $POR for every retired name: empty (amir_day's own S488 tail is Kit 3's dead code, named in README)"
# ---- 10: the data step (the kit's item_alias, copied out of the kit folder) -------------------------------------------------------------------
mkdir -p "$WALK/mods" && cp -p "$WALK/built/item_alias.py" "$WALK/mods/item_alias.py" || restore "the kit's module copy"
DOUT="$( cd "$FIN" && timeout 900 "$SPY" -B "$KDIR/data_s528.py" --db "$DBF" --modules "$WALK/mods" --finance "$FIN" --archive "$ING/archive" --readings "$SPN/readings" 2>&1 )"; DRC=$?
echo "$DOUT" | mask | cut -c1-300 | sed 's/^/   /'
[ "$DRC" = 0 ] && echo "$DOUT" | grep -q "^DATA_S528: " || restore "the data step did not run clean (exit $DRC)"
say "[10/15] the data step ran on the live database with the kit's item_alias (above: one line per ticked row, the summary after)"
# ---- 11: restart, health ------------------------------------------------------------------------------------------------------------------
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
c=$(health "http://127.0.0.1:8106/finance/stock/page/amir?count=1"); say "         /finance/stock/page/amir $c (302/401 = the login gate, expected)"
[ "$c" = 302 ] || [ "$c" = 401 ] || restore "the gated page answered $c"
c=$(health "http://127.0.0.1:8106/finance/stock/api/pad/amir/1"); say "         /finance/stock/api/pad/amir/1 $c (302/401 = the login gate, expected)"
[ "$c" = 302 ] || [ "$c" = 401 ] || restore "the gated board answered $c"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[11/15] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
# ---- 12-13: the state after, the live read-back --------------------------------------------------------------------------------------------
say "   the state AFTER placing (the words Amir and the owner see):"
state_print
mkdir -p "$R/rb/nosso"
RB="$( cd "$FIN" && FINANCE_DB="$DBF" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$R/rb/nosso" timeout 600 "$SPY" -B "$KDIR/state_s528.py" --finance "$FIN" --mode readback 2>&1 )"
echo "$RB" | mask | cut -c1-1200 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read of the live board"
say "[13/15] the live board (as the owner and as amir), the hub's step 7, Amir's step 6 and Needs-you read once (above)"
# ---- 14-15: nothing else moved ---------------------------------------------------------------------------------------------------------
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[14/15] nothing else moved (the must-not-move files, the crontab); healthz 200"
for f in "${ALL[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "[15/15] done · healthz 200 · backups: four .bak_S528_<from8>, $FIN/finance.db.bak_S528_$STAMP · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
