#!/bin/bash
# =============================================================================
#  install_S454_P4A.sh · kit S454_BILL_REGISTER, part 4 -- the server side (session 283, 03-Oct-2026; S454 10.2)
#  The medical PC's note of a refused text: marg_door takes it on the same address and with the same key as a file, before take(), and writes
#  one mi_file row refused by the PC with the reason. The owner's Needs-you, the reports tile and Darpan's card already read such a row. A
#  door nobody knocks on yet is harmless; the watcher that knocks (P4B_REFUSAL_WATCHER) is walked here end to end and delivered separately,
#  not before 04-Oct 13:00 IST (S454 10.3).
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S454_BILL_REGISTER):
#    bash <kit>/P4A_REFUSAL_DOOR/install_S454_P4A.sh             (DRY=1: every gate, the build and every walk; nothing placed.
#                                                                  KITS=<dir> the folder of the earlier kits; DUTYMAP=<file> the duty map v5.)
#
#  PATCHED ON THE BOX from the live bytes (make_s454p4a.py; every anchor exactly once; FROM -> TO pinned): /root/finance/marg_door.py
#  DATA: none (a finance.db backup is made all the same). RESTARTS clinic-finance only.
#  Not touched: finance_app.py, portal.py, tile_grants.json, sanjeevni_approvals.py, packs.py, asset_register.py, item_alias.py, stockmatch.py,
#  every other Sanjeevni file, the marg_ingest files, the crontab, the duty map, the medical PC.
# =============================================================================
set -u
KIT="S454_BILL_REGISTER"
PART="P4A_REFUSAL_DOOR"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/../..}"
DUTYMAP="${DUTYMAP:-$KDIR/../../../claude_code_briefs/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp; SHR=/root/shared; MRG=/root/marg_ingest
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s454p4a_walk_$STAMP"
declare -A FROM=( [marg_door.py]=598ba2df83f029d6f861e63190a62a33 )
declare -A TO=( [marg_door.py]=0 )
ORDER=(marg_door.py)
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/sanjeevni_approvals.py" "$FIN/packs.py" "$AST/asset_register.py" "$FIN/item_alias.py"
      "$FIN/stockmatch.py" "$FIN/supplier_msg.py" "$FIN/porders.py" "$FIN/porders_s454.py" "$FIN/order_sheet.py" "$FIN/scan_register.py" "$FIN/order_rules.py"
      "$FIN/stock_watch.py" "$FIN/stock_app.py" "$FIN/shelf_figure.py" "$FIN/purchase_app.py" "$FIN/amir_day.py" "$FIN/reports_tile.py" "$FIN/darpan_kal.py"
      "$MRG/marg_take.py" "$MRG/marg_ingest.py" "$MRG/signatures.json")
# the watchers the walk uses: NEW = part 4's (P4B, pinned), OLD = S397 as it runs on the medical PC; both with the S454 reader and the S259 pusher
W_NEW="$KITS/S454_BILL_REGISTER/P4B_REFUSAL_WATCHER/marg_watch.py"; W_NEW_MD5=20ec1602174cea5e2726d87797fa8e88
W_OLD="$KITS/S397_STOCK_TEXT/marg_watch.py"; W_OLD_MD5=81145aa7d7c8e9f7e23072cfab1ee620
W_TXT="$KITS/S454_BILL_REGISTER/P1_ORDER_SHEET_RECEPTION/medical/marg_txt.py"; W_TXT_MD5=ed17bb763c202f81cb8b3708fac61b52
W_PUSH="$KITS/S259_OFF_SWITCHES/medical/marg_push.py"; W_PUSH_MD5=566e189e986128fa2ebb341a78b9ab65
SVC=clinic-finance
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/13] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] && grep -q "part $PART" KIT_ID.txt || { say "!! [1/13] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask, openpyxl, werkzeug.serving" 2>/dev/null || { say "!! [1/13] the venv python lacks flask / openpyxl / werkzeug; nothing installed"; exit 1; }
for k in "$KITS/S403_PURCHASE_ORDERS_LIVE/walk_s403.py" "$KITS/S444_STAFF_SAFE/walk_s444.py" "$KITS/S452_AMIR_PANEL_FIXES/walk_s452.py" "$DUTYMAP" "$DBF" "$ADB" "$SPD"; do
  [ -f "$k" ] || { say "!! [1/13] $k must be reachable (KITS=$KITS, DUTYMAP=$DUTYMAP) - nothing installed"; exit 1; }
done
for p in "$W_NEW:$W_NEW_MD5" "$W_OLD:$W_OLD_MD5" "$W_TXT:$W_TXT_MD5" "$W_PUSH:$W_PUSH_MD5"; do
  [ "$(m5 "${p%%:*}")" = "${p##*:}" ] || { say "!! [1/13] ${p%%:*} is not ${p##*:} - nothing installed"; exit 1; }
done
"$SPY" -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('version')==5 else 1)" "$DUTYMAP" || { say "!! [1/13] the duty map is not v5 - nothing installed"; exit 1; }
say "[1/13] kit gates green (SUMS, KIT_ID part 4A, the venv, the earlier walks, the four watcher files at their pins, the duty map v5, the databases)"
. "$KDIR/PINS.sh" || { say "!! [1/13] PINS.sh missing - nothing installed"; exit 1; }
if [ "$(m5 "$FIN/marg_door.py")" = "${TO[marg_door.py]}" ]; then say "-- ALREADY INSTALLED: marg_door.py is at the kit's pin; $SVC $(systemctl is-active "$SVC")"; exit 0; fi
[ "$(m5 "$FIN/marg_door.py")" = "${FROM[marg_door.py]}" ] || { say "!! [2/13] $FIN/marg_door.py is $(m5 "$FIN/marg_door.py"), not its FROM pin - nothing installed"; exit 1; }
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
say "[2/13] marg_door.py at its FROM pin (S240's, 598ba2df)"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s454p4a.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
[ "$(m5 "$WALK/built/marg_door.py")" = "${TO[marg_door.py]}" ] || { say "!! [3/13] built marg_door.py is not the kit's pin - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/13] live bytes + anchored edits give exactly the kit's file"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && cp -p "$WALK/built/marg_door.py" "$WALK/cc/built_marg_door.py" && cp -p "$W_NEW" "$WALK/cc/watch_new.py"
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/13] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/13] compiles on /usr/bin/python3 and the venv python (the door, the walk and part 4's watcher; in a scratch copy)"
R="$WALK/run"
mkdir -p "$R/fin_new/finance_ui" "$R/fin_new/spine" "$R/fin_old/finance_ui" "$R/fin_old/spine" "$R/por" "$R/w" "$R/wn" "$R/wo" || exit 1
for side in fin_new fin_old; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
done
cp -p "$WALK/built/marg_door.py" "$R/fin_new/marg_door.py"
cp -p "$W_NEW" "$R/wn/marg_watch.py"; cp -p "$W_OLD" "$R/wo/marg_watch.py"
for d in wn wo; do cp -p "$W_TXT" "$R/$d/marg_txt.py"; cp -p "$W_PUSH" "$R/$d/marg_push.py"; done
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/13] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/13] scratch copies made (marg_door.py is not run by any cron)"
say "[6/13] (no report step: the walk's own sections are the figures)"
WOUT="$( cd "$R" && timeout 2400 "$VPY" -B "$KDIR/walk_s454p4.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --watch-new "$R/wn" --watch-old "$R/wo" --por "$R/por" \
         --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/scratch_spine.db" --work "$R/w" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S454P4 GREEN" || { say "!! [7/13] walk_s454p4 red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[7/13] walk_s454p4 green on scratch copies (the door, its readers, the watcher end to end); its negative controls red on the box as it is"
O="$WALK/old"; mkdir -p "$O"
cp -p "$KDIR/plan_old_s454p4a.py" "$KDIR/walks_old_s454p4a.py" "$O/"
"$VPY" -B "$O/plan_old_s454p4a.py" --work "$O" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --ast "$AST" --por "$POR" --shared "$SHR" --kits "$KITS" --db "$DBF" --adb "$ADB" \
  --spine "$SPD" --duty-map-old "$DUTYMAP" --duty-map "$DUTYMAP" --py "$VPY" --out "$O/plan.json" | sed 's/^/   /'
OOUT="$( cd "$O" && timeout 5400 "$VPY" -B "$O/walks_old_s454p4a.py" --plan "$O/plan.json" 2>&1 )"
echo "$OOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$OOUT" | grep -q "^WALKS_OLD_S454P4A GREEN" || { say "!! [8/13] the earlier walks are red beyond the named reds - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[8/13] the earlier walks (S403 ... S452): green on the patched files but for the named reds, each red on the box as it is too"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [9/13] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
[ "$(m5 "$FIN/marg_door.py")" = "${FROM[marg_door.py]}" ] || { say "!! [9/13] marg_door.py moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$DBF" "$FIN/finance.db.bak_S454_$STAMP" || { say "!! [9/13] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
BAK="$FIN/marg_door.py.bak_S454_598ba2df"
[ -e "$BAK" ] && BAK="$FIN/marg_door.py.bak_S454P4A_598ba2df"
\cp -p "$FIN/marg_door.py" "$BAK" || { say "!! [9/13] backup of marg_door.py failed - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[9/13] finance.db.bak_S454_$STAMP made (backup API); $BAK beside it; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring marg_door.py byte-identically"
  \cp -p "$BAK" "$FIN/marg_door.py"
  systemctl restart "$SVC" || true; sleep 8
  say "   $FIN/marg_door.py $(m5 "$FIN/marg_door.py") (FROM ${FROM[marg_door.py]})"
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S454_$STAMP"
  rm -rf "$WALK"; exit 1
}
\cp "$WALK/built/marg_door.py" "$FIN/marg_door.py" || restore "copy"
[ "$(m5 "$FIN/marg_door.py")" = "${TO[marg_door.py]}" ] || restore "md5 read-back"
say "[10/13] placed; md5 read back = the TO pin"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/porders /finance/darpan/kal /finance/reports/aaj /finance/clinic/marg/upload; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
c=$(health http://127.0.0.1:8106/finance/api/marg-file); say "         /finance/api/marg-file $c (no key: 401 is the door's own refusal, expected)"
[ "$c" = 401 ] || [ "$c" = 403 ] || restore "the machine door answered $c with no key"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
say "[11/13] $SVC active; healthz 200; the gated pages answer the gate; the machine door refuses a call with no key; nothing else moved"
say "[12/13] no data step"
md5sum "$FIN/marg_door.py"
rm -rf "$WALK"
say "[13/13] done"
say "$KIT part 4A: DONE"
