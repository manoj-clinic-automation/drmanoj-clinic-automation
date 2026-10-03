#!/bin/bash
# =============================================================================
#  install_S454_P3B.sh · kit S454_BILL_REGISTER, folder P3B_FIRST_DAY (session 283, 03-Oct-2026; S454 section 18 -- F-712, F-713)
#  What the first afternoon of use showed: "Ek scan mein ek hi bill." on the staff's two scan screens (a second bill in one scan cannot be seen
#  from what the asset app stores); the arrival button says "Save kijiye" while a line is short or missing; "P.L." dropped like PVT / LTD;
#  an order that arrived by its scan is on the way once on marg too; a credit note is a return in the spot count's reading; the owner's
#  agreement card says on what stock it was taken.
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S454_BILL_REGISTER):
#    bash <kit>/P3B_FIRST_DAY/install_S454_P3B.sh                (DRY=1: every gate, the build, the report and every walk; nothing placed.
#                                                                  KITS=<dir> names the folder of the earlier kits when this kit runs from a copy;
#                                                                  DUTYMAP=<file> the duty map v5 now in claude_code_briefs.)
#
#  PATCHED ON THE BOX from the live bytes (make_s454p3b.py; every anchor exactly once; FROM -> TO pinned):
#     /root/finance/porders_s454.py  order_sheet.py  scan_register.py  order_rules.py  stock_watch.py      (Sanjeevni's; no new file)
#  DATA: none (a finance.db backup is made all the same). RESTARTS clinic-finance only. The crons that run order_rules.py, stock_watch.py and
#  purchase_app.py as scripts are proven on scratch copies first (F-711), and one live tick of order_rules.py is run after placing.
#  Not touched: finance_app.py, portal.py, tile_grants.json, sanjeevni_approvals.py, packs.py, asset_register.py, item_alias.py, stockmatch.py,
#  supplier_msg.py, porders.py, purchase_app.py, stock_app.py, shelf_figure.py, amir_day.py, reports_tile.py, darpan_kal.py, order_sheet_pdf.py,
#  the marg_ingest files, the crontab, the duty map.
# =============================================================================
set -u
KIT="S454_BILL_REGISTER"
PART="P3B_FIRST_DAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/../..}"
DUTYMAP="${DUTYMAP:-$KDIR/../../../claude_code_briefs/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp; SHR=/root/shared; MRG=/root/marg_ingest
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s454p3b_walk_$STAMP"
declare -A FROM=( [porders_s454.py]=eadbc8d3582991fa36ef3fde83253126 [order_sheet.py]=ebe1eb4b327c1a784e20174cda0abd4b [scan_register.py]=8d100e60c467dab413830a251ef198fb
                  [order_rules.py]=1729e971982d0823f8d33b3976fa4d74 [stock_watch.py]=b429660ddc9a5291e261c5fa6fe652c0 )
declare -A TO=( [porders_s454.py]=0 [order_sheet.py]=0 [scan_register.py]=0 [order_rules.py]=0 [stock_watch.py]=0 )
ORDER=(porders_s454.py order_sheet.py scan_register.py order_rules.py stock_watch.py)
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/sanjeevni_approvals.py" "$FIN/packs.py" "$AST/asset_register.py" "$FIN/item_alias.py"
      "$FIN/stockmatch.py" "$FIN/supplier_msg.py" "$FIN/porders.py" "$FIN/purchase_app.py" "$FIN/stock_app.py" "$FIN/shelf_figure.py" "$FIN/amir_day.py"
      "$FIN/reports_tile.py" "$FIN/darpan_kal.py" "$FIN/order_sheet_pdf.py" "$MRG/marg_take.py" "$MRG/signatures.json")
SVC=clinic-finance
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/13] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] && grep -q "part $PART" KIT_ID.txt || { say "!! [1/13] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask, openpyxl" 2>/dev/null || { say "!! [1/13] the venv python lacks flask / openpyxl; nothing installed"; exit 1; }
for k in "$KITS/S403_PURCHASE_ORDERS_LIVE/walk_s403.py" "$KITS/S410_MEDICINE_ORDERING/walk_s410.py" "$KITS/S428_STOCK_WATCH/walk_s428.py" "$KITS/S440_SCAN_FLOW/walk_s440.py" \
         "$KITS/S444_STAFF_SAFE/walk_s444.py" "$KITS/S446_AMIR_STAGES_BILLS/walk_s446.py" "$KITS/S452_AMIR_PANEL_FIXES/walk_s452.py" \
         "$DUTYMAP" "$DBF" "$ADB" "$SPD"; do
  [ -f "$k" ] || { say "!! [1/13] $k must be reachable (KITS=$KITS, DUTYMAP=$DUTYMAP) - nothing installed"; exit 1; }
done
"$SPY" -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('version')==5 else 1)" "$DUTYMAP" || { say "!! [1/13] the duty map is not v5 - nothing installed"; exit 1; }
say "[1/13] kit gates green (SUMS, KIT_ID P3B, the venv's flask, the earlier walks, the duty map v5, the databases)"
. "$KDIR/PINS.sh" || { say "!! [1/13] PINS.sh missing - nothing installed"; exit 1; }
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the five files are at the kit's pins; $SVC $(systemctl is-active "$SVC")"; exit 0; fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/13] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since part 3; nothing installed"; exit 1; }
done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
say "[2/13] the five live files at their FROM pins (part 3's order_rules / stock_watch / order_sheet / porders_s454, part 2's scan_register)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s454p3b.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/13] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/13] live bytes + anchored edits give exactly the kit's files (five pins match)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/13] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/13] compiles on /usr/bin/python3 and the venv python (in a scratch copy)"
R="$WALK/run"
mkdir -p "$R/fin_new/finance_ui" "$R/fin_new/spine" "$R/fin_old/finance_ui" "$R/fin_old/spine" "$R/por" "$R/w" "$R/rr" "$R/sc" || exit 1
for side in fin_new fin_old; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/fin_new/$f"; done
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/13] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
# [5/13] the crons run these files as SCRIPTS: each command, as the crontab spells it, on scratch copies -- must exit 0 (part 1's fault, F-711)
SOUT=""
for side in fin_new fin_old; do
  copydb "$DBF" "$R/sc/$side.db"; copydb "$SPD" "$R/sc/${side}_spine.db"; copydb "$ADB" "$R/sc/${side}_assets.db"
  for cmd in "order_rules.py tick" "stock_watch.py job" "purchase_app.py rematch"; do
    o="$( cd "$R/$side" && env -u ORDER_TICK -u ORDER_TODAY -u SARVAM_API_KEY FINANCE_DB="$R/sc/$side.db" SPINE_DB="$R/sc/${side}_spine.db" ASSETS_DB="$R/sc/${side}_assets.db" \
          ORDER_PUSH_STUB="$R/sc/push_$side.jsonl" PORDERS_SOURCE=tables timeout 600 "$VPY" -B $cmd 2>&1 )"; rc=$?
    SOUT="$SOUT$side  $cmd  exit $rc  $(echo "$o" | tail -1 | mask | cut -c1-160)"$'\n'
    [ "$side" = fin_new ] && [ "$rc" != 0 ] && { echo "$o" | mask | tail -20 | sed 's/^/   /'; say "!! [5/13] '$cmd' as a script on the built files exits $rc - nothing installed"; rm -rf "$WALK"; exit 1; }
  done
done
echo "$SOUT" | sed 's/^/   /'
say "[5/13] the crons' own commands (order_rules.py tick, stock_watch.py job, purchase_app.py rematch) run as scripts on the built files and exit 0 (scratch copies)"
ROUT="$( cd "$R" && timeout 2400 "$VPY" -B "$KDIR/report_s454p3b.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$R/scratch_spine.db" --work "$R/rr" 2>&1 )"
echo "$ROUT" | mask | cut -c1-400 | sed 's/^/   /'
echo "$ROUT" | grep -q "^REPORT_S454P3B DONE" || { say "!! [6/13] S454 18's report did not finish - nothing installed"; rm -rf "$WALK"; exit 1; }
if echo "$ROUT" | grep -q "PAIR LOST by NEW only"; then say "!! [6/13] a link that exists would be lost - nothing installed"; rm -rf "$WALK"; exit 1; fi
if echo "$ROUT" | grep -q "PAIR MADE by NEW only" && [ "${PAIRS_READ:-0}" != 1 ]; then
  say "!! [6/13] the rule makes a new pair (above): read it before placing (PAIRS_READ=1 once it has been read and is right) - nothing installed"; rm -rf "$WALK"; exit 1
fi
say "[6/13] S454 18.3 / 18.4 / 18.5's report on today's data, on scratch copies (above)"
WOUT="$( cd "$R" && timeout 2400 "$VPY" -B "$KDIR/walk_s454p3b.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$R/scratch_spine.db" --work "$R/w" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S454P3B GREEN" || { say "!! [7/13] walk_s454p3b red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[7/13] walk_s454p3b green on scratch copies; its negative controls red on the box as it is (above)"
O="$WALK/old"; mkdir -p "$O"
cp -p "$KDIR/plan_old_s454p3b.py" "$KDIR/walks_old_s454p3b.py" "$O/"
"$VPY" -B "$O/plan_old_s454p3b.py" --work "$O" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --ast "$AST" --por "$POR" --shared "$SHR" --kits "$KITS" --db "$DBF" --adb "$ADB" \
  --spine "$SPD" --duty-map-old "$DUTYMAP" --duty-map "$DUTYMAP" --py "$VPY" --out "$O/plan.json" | sed 's/^/   /'
OOUT="$( cd "$O" && timeout 5400 "$VPY" -B "$O/walks_old_s454p3b.py" --plan "$O/plan.json" 2>&1 )"
echo "$OOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$OOUT" | grep -q "^WALKS_OLD_S454P3B GREEN" || { say "!! [8/13] the earlier walks are red beyond the named reds - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[8/13] the earlier walks (S403 ... S452): green on the patched files but for the named reds, each red on the box as it is too"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [9/13] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [9/13] $FIN/$f moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
done
copydb "$DBF" "$FIN/finance.db.bak_S454_$STAMP" || { say "!! [9/13] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$FIN/$f.bak_S454_${FROM[$f]:0:8}"
  [ -e "${BAK[$f]}" ] && BAK[$f]="$FIN/$f.bak_S454P3B_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [9/13] backup of $f failed - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[9/13] finance.db.bak_S454_$STAMP made (backup API); a .bak beside each of the five files; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S454_$STAMP"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[10/13] placed; md5 read back = the five TO pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/porders /finance/porders/s454/maal /finance/purchase/page/scans /finance/purchase/page/sarvam /finance/stock/page/count; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
say "[11/13] $SVC active; healthz 200; the gated pages answer the gate; nothing else moved"
TK="$( cd "$FIN" && FINANCE_DB="$DBF" timeout 600 "$VPY" -B "$FIN/order_rules.py" tick 2>&1 )"; rc=$?
echo "$TK" | tail -2 | mask | cut -c1-200 | sed 's/^/   live tick: /'
[ "$rc" = 0 ] || restore "the live order_rules.py tick exited $rc"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz after the live tick"
say "[12/13] no data step; one live tick of order_rules.py exits 0 (above)"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "[13/13] done"
say "$KIT P3B: DONE"
