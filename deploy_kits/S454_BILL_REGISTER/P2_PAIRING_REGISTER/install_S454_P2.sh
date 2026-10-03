#!/bin/bash
# =============================================================================
#  install_S454_P2.sh · kit S454_BILL_REGISTER, part 2 (session 283, 03-Oct-2026; S454 sections 5, 6, 7, 8, 12 -- D662 D663 D665, F-690 F-691)
#  A scan is paired with its Marg bill on what a scan reads well; Amir is asked nothing new; the owner's month register; Vendor payments for the
#  owner and Shavez only; manoj.returns_ok reads the owner's own rule.
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S454_BILL_REGISTER):
#    bash <kit>/P2_PAIRING_REGISTER/install_S454_P2.sh            (DRY=1: every gate, the build, the rules report and every walk; nothing placed.
#                                                                  KITS=<dir> names the folder of the earlier kits when this kit runs from a copy;
#                                                                  DUTYMAP_OLD=<file> the duty map v4 now in claude_code_briefs.)
#
#  PATCHED ON THE BOX from the live bytes (make_s454p2.py; every anchor exactly once; FROM -> TO pinned):
#     /root/finance/purchase_app.py  porders.py  porders_s454.py  order_sheet.py  amir_day.py  reports_tile.py      (Sanjeevni's)
#  NEW: /root/finance/scan_register.py
#  DATA (finance.db, backed up first): one pass of the matcher under the new rules (the auto-links it makes, audited auto_link); the owner's
#     returns rule's count kept as setting returns.pending_ok; part 2's four settings at their defaults on first read.
#  NOT ON THE BOX: claude_code_briefs/DUTY_MAP.json / .md v5 -- the repository's (the app reads them from /root/deploy/repo after the pull).
#  RESTARTS clinic-finance only. Not touched: finance_app.py, portal.py, tile_grants.json, sanjeevni_approvals.py, packs.py, asset_register.py,
#  item_alias.py, stockmatch.py, stock_app.py, stock_watch.py, supplier_msg.py, order_rules.py, darpan_kal.py, the marg_ingest files, the crontab.
# =============================================================================
set -u
KIT="S454_BILL_REGISTER"
PART="P2_PAIRING_REGISTER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/../..}"
DUTYMAP_OLD="${DUTYMAP_OLD:-$KDIR/../../../claude_code_briefs/DUTY_MAP.json}"
DUTYMD_OLD="${DUTYMD_OLD:-$KDIR/../../../claude_code_briefs/DUTY_MAP.md}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp; SHR=/root/shared; MRG=/root/marg_ingest
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s454p2_walk_$STAMP"
declare -A FROM=( [purchase_app.py]=591432422d6b06af3dff886a8a0fc378 [porders.py]=d4842f2c0f40a6ff69bd9a6d0425778f [porders_s454.py]=c2608914e56b0f7ce049d93aeed23d39
                  [order_sheet.py]=cffbeef3f4405132ab1861ffc146bea9 [amir_day.py]=85f208d0d64def40fb5a02e02c531284 [reports_tile.py]=8a9870414cf299b0396bec4bc937ef04 )
declare -A TO=( [purchase_app.py]=0 [porders.py]=0 [porders_s454.py]=0 [order_sheet.py]=0 [amir_day.py]=0 [reports_tile.py]=0 [scan_register.py]=0 )
ORDER=(purchase_app.py porders.py porders_s454.py order_sheet.py amir_day.py reports_tile.py scan_register.py)
NEWF=(scan_register.py)
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/sanjeevni_approvals.py" "$FIN/packs.py" "$AST/asset_register.py" "$FIN/item_alias.py"
      "$FIN/stockmatch.py" "$FIN/stock_app.py" "$FIN/stock_watch.py" "$FIN/supplier_msg.py" "$FIN/order_rules.py" "$FIN/darpan_kal.py" "$MRG/marg_take.py"
      "$MRG/signatures.json")
SVC=clinic-finance
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] && grep -q "part $PART" KIT_ID.txt || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask, openpyxl" 2>/dev/null || { say "!! [1/12] the venv python lacks flask / openpyxl; nothing installed"; exit 1; }
for k in "$KITS/S403_PURCHASE_ORDERS_LIVE/walk_s403.py" "$KITS/S410_MEDICINE_ORDERING/walk_s410.py" "$KITS/S439_SCANS_SMS_SCROLL/walk_s439.py" "$KITS/S440_SCAN_FLOW/walk_s440.py" \
         "$KITS/S441_SCAN_RATE/walk_s441.py" "$KITS/S444_STAFF_SAFE/walk_s444.py" "$KITS/S446_AMIR_STAGES_BILLS/walk_s446.py" "$KITS/S452_AMIR_PANEL_FIXES/walk_s452.py" \
         "$DUTYMAP_OLD" "$DUTYMD_OLD" "$DBF" "$ADB" "$SPD" "$KDIR/DUTY_MAP.json" "$KDIR/DUTY_MAP.md"; do
  [ -f "$k" ] || { say "!! [1/12] $k must be reachable (KITS=$KITS, DUTYMAP_OLD=$DUTYMAP_OLD) - nothing installed"; exit 1; }
done
say "[1/12] kit gates green (SUMS, KIT_ID part 2, the venv's flask, the earlier walks, the duty maps, the databases)"
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the seven files are at the kit's pins; $SVC $(systemctl is-active "$SVC")"; exit 0; fi
for f in "${ORDER[@]}"; do
  case " ${NEWF[*]} " in *" $f "*) [ -e "$FIN/$f" ] && { say "!! [2/12] $FIN/$f exists already - nothing installed"; exit 1; }; continue;; esac
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/12] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since part 1; nothing installed"; exit 1; }
done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
say "[2/12] the six live files at their FROM pins, scan_register.py absent"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s454p2.py --finance "$FIN" --kit "$KDIR" --dutymap-json "$DUTYMAP_OLD" --dutymap-md "$DUTYMD_OLD" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/12] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
for f in DUTY_MAP.json DUTY_MAP.md; do cmp -s "$WALK/built/$f" "$KDIR/$f" || { say "!! [3/12] the built $f is not the kit's $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/12] live bytes + anchored edits give exactly the kit's files (seven pins match); DUTY_MAP v5 = the kit's"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/12] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/12] compiles on /usr/bin/python3 and the venv python (in a scratch copy)"
R="$WALK/run"
mkdir -p "$R/fin_new/finance_ui" "$R/fin_new/spine" "$R/fin_old/finance_ui" "$R/fin_old/spine" "$R/por" "$R/w" "$R/rr" "$R/pictures" || exit 1
for side in fin_new fin_old; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/fin_new/$f"; done
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" || { say "!! [5/12] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
ROUT="$( cd "$R" && timeout 1500 "$VPY" -B "$KDIR/rules_report_s454p2.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --db "$R/scratch.db" --adb "$R/scratch_assets.db" --work "$R/rr" 2>&1 )"
echo "$ROUT" | mask | cut -c1-1200 | sed 's/^/   /'
echo "$ROUT" | grep -q "^RULES_REPORT GREEN" || { say "!! [5/12] the rules report is red (a suspect pair, or a side failed) - STOP, nothing installed (S454 5)"; rm -rf "$WALK"; exit 1; }
say "[5/12] S454 5's report on September, on scratch copies: no new pair is suspect (above)"
WOUT="$( cd "$R" && timeout 2400 "$VPY" -B "$KDIR/walk_s454p2.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --por "$R/por" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --work "$R/w" --duty-map-new "$KDIR/DUTY_MAP.json" --duty-map-old "$DUTYMAP_OLD" --pictures "$R/pictures" 2>&1 )"
echo "$WOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S454P2 GREEN" || { say "!! [6/12] walk_s454p2 red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/12] walk_s454p2 green on scratch copies; its negative controls red on the box as it is (above)"
O="$WALK/old"; mkdir -p "$O"
cp -p "$KDIR/plan_old_s454p2.py" "$KDIR/walks_old_s454p2.py" "$O/"
copydb "$SPD" "$R/spine.db" || true
"$VPY" -B "$O/plan_old_s454p2.py" --work "$O" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --ast "$AST" --por "$POR" --shared "$SHR" --kits "$KITS" --db "$DBF" --adb "$ADB" \
  --spine "$SPD" --duty-map-old "$DUTYMAP_OLD" --duty-map "$KDIR/DUTY_MAP.json" --py "$VPY" --out "$O/plan.json" | sed 's/^/   /'
OOUT="$( cd "$O" && timeout 5400 "$VPY" -B "$O/walks_old_s454p2.py" --plan "$O/plan.json" 2>&1 )"
echo "$OOUT" | mask | cut -c1-900 | sed 's/^/   /'
echo "$OOUT" | grep -q "^WALKS_OLD_S454P2 GREEN" || { say "!! [7/12] the earlier walks are red beyond the named reds - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[7/12] the earlier walks (S403 ... S452): green on the patched files but for the named reds, each red on the box as it is too"
[ -n "${PICS_OUT:-}" ] && mkdir -p "$PICS_OUT" && cp -p "$R/pictures"/* "$PICS_OUT/" 2>/dev/null
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [8/12] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  case " ${NEWF[*]} " in *" $f "*) [ -e "$FIN/$f" ] && { say "!! [8/12] $FIN/$f appeared during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }; continue;; esac
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [8/12] $FIN/$f moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
done
copydb "$DBF" "$FIN/finance.db.bak_S454_$STAMP" || { say "!! [8/12] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  case " ${NEWF[*]} " in *" $f "*) continue;; esac
  BAK[$f]="$FIN/$f.bak_S454_${FROM[$f]:0:8}"
  [ -e "${BAK[$f]}" ] && BAK[$f]="$FIN/$f.bak_S454P2_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [8/12] backup of $f failed - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[8/12] finance.db.bak_S454_$STAMP made (backup API); a .bak beside each of the six files; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do
    case " ${NEWF[*]} " in *" $f "*) rm -f "$FIN/$f";; *) \cp -p "${BAK[$f]}" "$FIN/$f";; esac
  done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f" || echo absent) (FROM ${FROM[$f]:-new})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · the database backup stays: $FIN/finance.db.bak_S454_$STAMP"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[9/12] placed; md5 read back = the seven TO pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/porders /finance/purchase/page/scans /finance/purchase/page/pay /finance/amir /finance/reports/aaj /finance/purchase/page/sarvam; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
say "[10/12] $SVC active; healthz 200; the gated pages answer the gate; nothing else moved"
DOUT="$( cd "$FIN" && FINANCE_DB="$DBF" ASSETS_DB="$ADB" "$VPY" -B "$KDIR/data_s454p2.py" --db "$DBF" --finance "$FIN" 2>&1 )"
echo "$DOUT" | mask | sed 's/^/   /'
echo "$DOUT" | grep -q "^S454 P2 data done" || restore "the data step"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz after the data step"
say "[11/12] the data step done (above)"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "[12/12] done"
say "$KIT part 2: DONE"
