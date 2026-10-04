#!/bin/bash
# =============================================================================
#  install_S470_ORDER_ON_SPINE.sh · kit S470_ORDER_ON_SPINE (Sanjeevni, session 285, 04-Oct-2026; D672, D673; F-718, F-719)
#  The medicine order engine reads the spine (its sale rate, Marg's stock, the supplier and the lot) behind order.engine_source; the nightly
#  trial keeps and scores the list the engine really made; one line a week on the owner's card. No staff screen changes.
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S470_ORDER_ON_SPINE):
#    bash <kit>/install_S470_ORDER_ON_SPINE.sh      (DRY=1: every gate, the build, the compare and every walk; nothing placed.
#                                                    KITS=<dir> the folder of the earlier kits when this kit runs from a copy;
#                                                    DUTYMAP=<file> the duty map now in claude_code_briefs; OLDWALKS=0 skips step 9 on a re-run
#                                                    of a DRY run that already showed it green -- never on the placing run.)
#
#  PATCHED ON THE BOX from the live bytes (make_s470.py; every anchor exactly once; FROM -> TO pinned):
#     /root/finance/order_rules.py  purchase_app.py (ONE edit)  porders_s454.py  spine/spine_read.py  spine/selftest_spine.py
#  REPLACED WHOLE by the kit's file (FROM pinned): /root/finance/spine/order_rehearsal.py
#  DATA (after a finance.db backup by the backup API): six rows in `setting` (INSERT OR IGNORE); the trial keeps each day from 28-Sep to
#  yesterday in spine/orders/ (S341's files of those nights copied to orders/before_S470/ first). spine.db is never written.
#  RESTARTS clinic-finance only. Not touched: finance_app.py, portal.py, tile_grants.json, shelf_figure.py, stock_watch.py, order_sheet.py,
#  porders.py, packs.py, asset_register.py, spine/spine_build.py, the crontab, the duty map.
# =============================================================================
set -u
KIT="S470_ORDER_ON_SPINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
DUTYMAP="${DUTYMAP:-$KDIR/../../claude_code_briefs/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp; SHR=/root/shared
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s470_walk_$STAMP"
KEEP_FROM="2026-09-28"
declare -A FROM=( [order_rules.py]=734fc6bcd67bb23da1bea2a6e927fcad [purchase_app.py]=979391b6e191e0d2468f3db6fc57366e [porders_s454.py]=c3562c5bc5602ecdb32e416a231ba30c
                  [spine/spine_read.py]=ab55344ee280b0b4847a45cebe6d3843 [spine/selftest_spine.py]=bfa607b980e4e838dfc7198f0bc7c9c9
                  [spine/order_rehearsal.py]=02582fbea29f51606a6ba8bb8694d3fc )
declare -A TO=( [order_rules.py]=0 [purchase_app.py]=0 [porders_s454.py]=0 [spine/spine_read.py]=0 [spine/selftest_spine.py]=0 [spine/order_rehearsal.py]=0 )
# placed in this order: purchase_app first (its new argument is optional), the read door before the engine that reads it, order_rules last
ORDER=(purchase_app.py spine/spine_read.py spine/selftest_spine.py spine/order_rehearsal.py porders_s454.py order_rules.py)
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/shelf_figure.py" "$FIN/stock_watch.py" "$FIN/order_sheet.py" "$FIN/porders.py" "$FIN/packs.py"
      "$AST/asset_register.py" "$FIN/spine/spine_build.py" "$FIN/spine/marg_read.py" "$FIN/sanjeevni_approvals.py" "$FIN/supplier_msg.py" "$FIN/stock_app.py")
SVC=clinic-finance
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/15] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/15] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask, openpyxl" 2>/dev/null || { say "!! [1/15] the venv python lacks flask / openpyxl; nothing installed"; exit 1; }
for k in "$KITS/S403_PURCHASE_ORDERS_LIVE/walk_s403.py" "$KITS/S410_MEDICINE_ORDERING/walk_s410.py" "$KITS/S428_STOCK_WATCH/walk_s428.py" "$KITS/S440_SCAN_FLOW/walk_s440.py" \
         "$KITS/S444_STAFF_SAFE/walk_s444.py" "$KITS/S446_AMIR_STAGES_BILLS/walk_s446.py" "$KITS/S452_AMIR_PANEL_FIXES/walk_s452.py" \
         "$KITS/S454_BILL_REGISTER/P3_SHELF_FIGURE/walk_s454p3.py" "$KITS/S454_BILL_REGISTER/P1C_SHEET_PAGE_AND_PHONE/walk_s454p1c.py" "$DUTYMAP" "$DBF" "$ADB" "$SPD"; do
  [ -f "$k" ] || { say "!! [1/15] $k must be reachable (KITS=$KITS, DUTYMAP=$DUTYMAP) - nothing installed"; exit 1; }
done
"$SPY" -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('version')==5 else 1)" "$DUTYMAP" || { say "!! [1/15] the duty map is not v5 - nothing installed"; exit 1; }
say "[1/15] kit gates green (SUMS, KIT_ID, the venv's flask, the earlier walks, the duty map v5 -- not edited by this kit --, the databases)"
. "$KDIR/PINS.sh" || { say "!! [1/15] PINS.sh missing - nothing installed"; exit 1; }
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the six files are at the kit's pins; $SVC $(systemctl is-active "$SVC")"; exit 0; fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/15] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }
done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/15] the six live files at their FROM pins (the brief's section 6)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s470.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/15] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
cmp -s "$WALK/built/spine/order_rehearsal.py" "$KDIR/order_rehearsal.py" || { say "!! [3/15] the built order_rehearsal.py is not the kit's file - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/15] live bytes + anchored edits give exactly the kit's files (six pins match; order_rehearsal.py is the kit's own file)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$(echo "$f" | tr '/' '_')"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/15] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/15] compiles on /usr/bin/python3 and the venv python (in a scratch copy)"
R="$WALK/run"
mkdir -p "$R/fin_new/finance_ui" "$R/fin_new/spine" "$R/fin_old/finance_ui" "$R/fin_old/spine" "$R/por" "$R/w" "$R/sc" "$R/orders" || exit 1
for side in fin_new fin_old; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/fin_new/$f"; done
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/15] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
# [5/15] the crons run these files as SCRIPTS: each command, as the crontab spells it, on scratch copies -- must exit 0 (F-711)
SOUT=""
for side in fin_new fin_old; do
  copydb "$DBF" "$R/sc/$side.db"; copydb "$SPD" "$R/sc/${side}_spine.db"; copydb "$ADB" "$R/sc/${side}_assets.db"; mkdir -p "$R/sc/orders_$side"
  for cmd in "order_rules.py tick" "stock_watch.py job" "purchase_app.py rematch"; do
    o="$( cd "$R/$side" && env -u ORDER_TICK -u ORDER_TODAY -u SARVAM_API_KEY FINANCE_DB="$R/sc/$side.db" SPINE_DB="$R/sc/${side}_spine.db" ASSETS_DB="$R/sc/${side}_assets.db" \
          ORDER_PUSH_STUB="$R/sc/push_$side.jsonl" PORDERS_SOURCE=tables timeout 600 "$VPY" -B $cmd 2>&1 )"; rc=$?
    SOUT="$SOUT$side  $cmd  exit $rc  $(echo "$o" | tail -1 | mask | cut -c1-150)"$'\n'
    [ "$side" = fin_new ] && [ "$rc" != 0 ] && { echo "$o" | mask | tail -20 | sed 's/^/   /'; say "!! [5/15] '$cmd' as a script on the built files exits $rc - nothing installed"; rm -rf "$WALK"; exit 1; }
  done
done
o="$( cd "$R/fin_new/spine" && timeout 600 "$VPY" -B order_rehearsal.py --spine "$R/sc/fin_new_spine.db" --finance-db "$R/sc/fin_new.db" --out "$R/sc/orders_fin_new" 2>&1 )"; rc=$?
SOUT="${SOUT}fin_new  spine/order_rehearsal.py  exit $rc  $(echo "$o" | sed -n '2p' | mask | cut -c1-150)"$'\n'
[ "$rc" = 0 ] || { echo "$o" | mask | tail -20 | sed 's/^/   /'; say "!! [5/15] order_rehearsal.py as a script exits $rc - nothing installed"; rm -rf "$WALK"; exit 1; }
echo "$SOUT" | sed 's/^/   /'
say "[5/15] the crons' own commands (order_rules.py tick, stock_watch.py job, purchase_app.py rematch, spine/order_rehearsal.py) run as scripts on the built files and exit 0"
ST="$( cd "$R/fin_new/spine" && timeout 900 "$VPY" -B selftest_spine.py 2>&1 | tail -1 )"
echo "$ST" | grep -q "^SELFTEST OK" || { say "!! [6/15] the spine's selftest on the built files: $ST - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/15] the spine's own selftest on the built files: $ST (the box as it is: $( cd "$R/fin_old/spine" && timeout 900 "$VPY" -B selftest_spine.py 2>&1 | tail -1 ))"
copydb "$DBF" "$R/cmp.db"; copydb "$SPD" "$R/cmp_spine.db"
COUT="$( cd "$R" && timeout 1800 "$VPY" -B "$KDIR/compare_s470.py" --fin "$R/fin_new" --db "$R/cmp.db" --spine "$R/cmp_spine.db" 2>&1 )"
echo "$COUT" | mask | cut -c1-400 | sed 's/^/   /'
echo "$COUT" | grep -q "^COMPARE_S470 DONE" || { say "!! [7/15] the compare did not finish - nothing installed"; rm -rf "$WALK"; exit 1; }
KOUT="$( cd "$R/fin_new/spine" && timeout 900 "$VPY" -B order_rehearsal.py --spine "$R/cmp_spine.db" --finance-db "$R/cmp.db" --out "$R/orders" --from "$KEEP_FROM" 2>&1 | tail -4; \
         "$SPY" -B "$KDIR/data_s470.py" kept --orders "$R/orders" 2>&1 )"
echo "$KOUT" | mask | cut -c1-400 | sed 's/^/   /'
echo "$KOUT" | grep -q "^DATA_S470 kept DONE" || { say "!! [7/15] the trial's first week on scratch copies did not finish - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[7/15] the compare on today's data, on scratch copies (above): the spine's closing against stock_snapshot, the plan on spine against the plan on tables, no_supplier; the trial's first week kept on a scratch folder"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s470.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$R/scratch_spine.db" --work "$R/w" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S470 GREEN" || { say "!! [8/15] walk_s470 red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[8/15] walk_s470 green on scratch copies; its negative controls red on the box as it is (above)"
if [ "${OLDWALKS:-1}" = 1 ] || [ "${DRY:-0}" != 1 ]; then
  O="$WALK/old"; mkdir -p "$O"
  cp -p "$KDIR/plan_old_s470.py" "$KDIR/walks_old_s470.py" "$O/"
  "$VPY" -B "$O/plan_old_s470.py" --work "$O" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --ast "$AST" --por "$POR" --shared "$SHR" --kits "$KITS" --db "$DBF" --adb "$ADB" \
    --spine "$SPD" --duty-map-old "$DUTYMAP" --duty-map "$DUTYMAP" --py "$VPY" --out "$O/plan.json" | sed 's/^/   /'
  OOUT="$( cd "$O" && timeout 9000 "$VPY" -B "$O/walks_old_s470.py" --plan "$O/plan.json" 2>&1 )"
  echo "$OOUT" | mask | cut -c1-900 | sed 's/^/   /'
  echo "$OOUT" | grep -q "^WALKS_OLD_S470 GREEN" || { say "!! [9/15] the earlier walks show a red that the box as it is does not - nothing installed"; rm -rf "$WALK"; exit 1; }
  say "[9/15] the earlier walks (S403 ... S452, S454's): on the patched files every red is red, word for word, on the box as it is too -- but I7, the one S470 itself makes (named above)"
else
  say "[9/15] the earlier walks SKIPPED on this dry run (OLDWALKS=0)"
fi
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [10/15] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [10/15] $FIN/$f moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
done
copydb "$DBF" "$FIN/finance.db.bak_S470_$STAMP" || { say "!! [10/15] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$FIN/$f.bak_S470_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [10/15] backup of $f failed - nothing placed"; rm -rf "$WALK"; exit 1; }
  [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [10/15] the backup of $f does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[10/15] finance.db.bak_S470_$STAMP made (backup API); a .bak_S470_<from8> beside each of the six files, read back; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S470_$STAMP"
  say "   the six setting rows and the kept files in spine/orders (if the data step had run) are left: the old files read none of them"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[11/15] placed; md5 read back = the six TO pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/porders "/finance/porders?old=1" /finance/amir /finance/stock/page/count; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
say "[12/15] $SVC active (restarted $T0); healthz 200; the gated pages answer the gate; nothing else moved; the crontab is as it was"
DOUT="$( "$VPY" -B "$KDIR/data_s470.py" settings --fin "$FIN" --db "$DBF" 2>&1 )"
echo "$DOUT" | sed 's/^/   /'
echo "$DOUT" | grep -q "^DATA_S470 settings DONE" || restore "the six setting rows"
KOUT="$( cd "$FIN/spine" && timeout 900 "$VPY" -B order_rehearsal.py --from "$KEEP_FROM" 2>&1 | tail -4; "$SPY" -B "$KDIR/data_s470.py" kept --orders "$FIN/spine/orders" 2>&1 )"
echo "$KOUT" | mask | cut -c1-400 | sed 's/^/   /'
echo "$KOUT" | grep -q "^DATA_S470 kept DONE" || restore "the trial's first week"
say "[13/15] the data step: six setting rows; the trial kept each day from $KEEP_FROM to yesterday (above)"
TK="$( cd "$FIN" && FINANCE_DB="$DBF" timeout 600 "$VPY" -B "$FIN/order_rules.py" tick 2>&1 )"; rc=$?
echo "$TK" | tail -2 | mask | cut -c1-200 | sed 's/^/   live tick: /'
[ "$rc" = 0 ] || restore "the live order_rules.py tick exited $rc"
EN="$( cd "$FIN" && FINANCE_DB="$DBF" timeout 600 "$VPY" -B -c "import sqlite3, os, order_rules as o; c = sqlite3.connect('file:%s?mode=ro' % os.environ['FINANCE_DB'], uri=True); c.row_factory = sqlite3.Row; x = o._snapshot_inputs(c, o._today()); print('engine=%s items=%d with_pace=%d with_supplier=%d as_on=%s' % (o._s470_engine(), len(x[1]), len(x[2]), len(x[3]), x[0]))" 2>&1 | tail -1 )"
say "   live read (read-only): $EN"
echo "$EN" | grep -q "^engine=spine " || restore "the live engine does not read the spine: $EN"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz after the live tick"
say "[14/15] one live tick of order_rules.py exits 0; the live engine reads the spine (above); healthz 200"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "[15/15] done"
say "$KIT: DONE"
