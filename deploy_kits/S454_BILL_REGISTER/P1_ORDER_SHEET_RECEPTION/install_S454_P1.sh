#!/bin/bash
# =============================================================================
#  install_S454_P1.sh · kit S454_BILL_REGISTER, part 1 (session 283, 03-Oct-2026; D666, D668, D669 -- D650 / D640 / D643 / D648 / D626 served)
#  Sanjeevni: the order comes from Darpan's Marg sheet; reception orders, receives and scans on one simple screen
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S454_BILL_REGISTER):
#    SHEET=/tmp/s454p1/MARG_ORDER_SHEET_02-10-2026.txt bash <kit>/P1_ORDER_SHEET_RECEPTION/install_S454_P1.sh
#  (DRY=1 runs every gate, the build and every walk on scratch copies, and places nothing; SHEET is then not needed. KITS=<dir> names the
#   folder holding the earlier kits when this kit runs from a copy; DUTYMAP_OLD=<file> the duty map now in claude_code_briefs (v3).)
#
#   * /finance/porders: "Aaj ka kaam" -- the scan button and a row per kind of work (Order karna hai · Maal aaya? · Bill scan karna hai ·
#     Photo dekh kar bataiye), one task at a time (porders_s454.py); the old page one tap away (?old=1); the owner's cards and settings there.
#   * Darpan's PENDING ORDERS (PURCHASE), converted on the medical PC (marg_txt S454, delivered by Drive, not by this script), taken by the
#     door (signatures.json: ORDER_PENDING) and loaded at once (order_sheet.py, marg_take's hook); the comparison with the system's own list.
#   * WhatsApp through the reception phone's queue as kind 'order' (supplier_msg: payment counts untouched, F-702 handout gap); one
#     reminder a day (order_rules); arrival by the bill's scan (order_sheet's tie, run from the cron as well); the printed A4 order sheet.
#   * The first load: Darpan's sheet of 02-Oct, as already ordered (first_load_s454.py -- the file from /tmp, never kept in the kit).
#
#  PATCHED ON THE BOX from the live bytes (make_s454p1.py; every anchor exactly once; FROM -> TO pins checked):
#     /root/finance/porders.py  order_rules.py  supplier_msg.py  purchase_app.py  darpan_kal.py  darpan_kal.html     (Sanjeevni's)
#     /root/marg_ingest/marg_take.py  signatures.json                                                                 (Sanjeevni's)
#  NEW: /root/finance/order_sheet.py  porders_s454.py  order_sheet_pdf.py
#  CRONTAB: order_rules' own line only (S410_MEDICINE_ORDERING): every ten minutes 05:00-21:50, so the tie and Marg's clearing never wait
#     for a page and the one reminder fires at its time; backed up first.
#  DATA (finance.db, backed up first): tables made on first use (order_sheet, order_sheet_line, order_scan_tie, s454_line_edit,
#     s454_scan_answer, s454_later, s454_paper_missing), columns added (purchase_order: supplier_norm, ext_ref, order_src, order_via,
#     sheet_id; supplier_msg: handed_at), the S454 settings (their defaults); the first load's rows and its ten paper orders.
#  RESTARTS clinic-finance only. Not touched: finance_app.py, portal.py, tile_grants.json, finance_ui/, sanjeevni_approvals.py, packs.py,
#  asset_register.py, item_alias.py, stockmatch.py, the medical PC (by Drive, after this).
# =============================================================================
set -u
KIT="S454_BILL_REGISTER"
PART="P1_ORDER_SHEET_RECEPTION"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/../..}"
DUTYMAP="$KDIR/DUTY_MAP.json"
DUTYMAP_OLD="${DUTYMAP_OLD:-$KDIR/../../../claude_code_briefs/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; AST="$ROOT/assetapp"; SHR="$ROOT/shared"; MRG="$ROOT/marg_ingest"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s454p1_walk_$STAMP"
declare -A FROM=( [porders.py]=3620b374a8fb3ac4988b8e6525795f84 [order_rules.py]=00a60efb515972313839662ff7f83495 [supplier_msg.py]=5cc35d2af444b5ab1996f636db8e54cf
                  [purchase_app.py]=341c663e52076f0ee264c356b49cf49e [darpan_kal.py]=377ffd63786261cef4a6113482d43bb5 [darpan_kal.html]=9269afb04a454b626895a27666032752
                  [marg_take.py]=21e37b0e6fa6505a8825b32b7c24d41d [signatures.json]=b2dcb2115a208bff81fac1c37c839428 )
declare -A TO=( [porders.py]=d4842f2c0f40a6ff69bd9a6d0425778f [order_rules.py]=d29efa8e6425fa359ea28d38c0758ccc [supplier_msg.py]=fc6c1724d6da4e1d04897b60d61c13b8 [purchase_app.py]=591432422d6b06af3dff886a8a0fc378 [darpan_kal.py]=911cf637a288fad85c75e54227149633 [darpan_kal.html]=c20ab05d8484e37a667ddae32a4c792b [marg_take.py]=b41195e4ce853272ecf25b06343e3e16 [signatures.json]=64943ac6719a0f2ee06a15ef56d8c3d1 [order_sheet.py]=4cf2f231ef026904d1ae42754846aea7 [porders_s454.py]=05716f3c040478d09fd2016561c7c99c [order_sheet_pdf.py]=9c28df38435a25d7e1d65c34b8d43ec9 )
ORDER=(porders.py order_rules.py supplier_msg.py purchase_app.py darpan_kal.py darpan_kal.html marg_take.py signatures.json order_sheet.py porders_s454.py order_sheet_pdf.py)
NEWF=(order_sheet.py porders_s454.py order_sheet_pdf.py)
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/sanjeevni_approvals.py" "$FIN/packs.py" "$AST/asset_register.py" "$FIN/item_alias.py"
      "$FIN/stockmatch.py" "$FIN/amir_day.py" "$FIN/reports_tile.py" "$FIN/stock_app.py" "$FIN/stock_watch.py")
SVC=clinic-finance
CRON_TAG="# S410_MEDICINE_ORDERING"
CRON_OLD="0,30 5-17 * * * cd /root/finance && FINANCE_DB=/root/finance/finance.db /root/wa/venv/bin/python3 -B /root/finance/order_rules.py tick >> /root/finance/order_rules.log 2>&1 # S410_MEDICINE_ORDERING"
CRON_NEW="*/10 5-21 * * * cd /root/finance && FINANCE_DB=/root/finance/finance.db /root/wa/venv/bin/python3 -B /root/finance/order_rules.py tick >> /root/finance/order_rules.log 2>&1 # S410_MEDICINE_ORDERING -- S454: every ten minutes, 05:00-21:50"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
dest() { case "$1" in marg_take.py|signatures.json) echo "$MRG/$1";; *) echo "$FIN/$1";; esac; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/11] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] && grep -q "part $PART" KIT_ID.txt || { say "!! [1/11] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask, openpyxl" 2>/dev/null || { say "!! [1/11] the venv python lacks flask / openpyxl; nothing installed"; exit 1; }
for k in "$KITS/S403_PURCHASE_ORDERS_LIVE/walk_s403.py" "$KITS/S410_MEDICINE_ORDERING/walk_s410.py" "$KITS/S440_SCAN_FLOW/walk_s440.py" "$KITS/S441_SCAN_RATE/walk_s441.py" \
         "$KITS/S444_STAFF_SAFE/walk_s444.py" "$KITS/S446_AMIR_STAGES_BILLS/walk_s446.py" "$KITS/S452_AMIR_PANEL_FIXES/walk_s452.py" "$KITS/S446_AMIR_STAGES_BILLS/medical/marg_txt.py" \
         "$DUTYMAP" "$DUTYMAP_OLD" "$DBF" "$ADB" "$SPD" "$KDIR/medical/marg_txt.py"; do
  [ -f "$k" ] || { say "!! [1/11] $k must be reachable (KITS=$KITS, DUTYMAP_OLD=$DUTYMAP_OLD) - nothing installed"; exit 1; }
done
"$SPY" -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); assert d.get('kit')=='$KIT' and d.get('version')==4" "$DUTYMAP" \
  || { say "!! [1/11] $DUTYMAP is not this kit's duty map (v4) - nothing installed"; exit 1; }
if [ "${DRY:-0}" != 1 ]; then
  [ -f "${SHEET:-}" ] || { say "!! [1/11] SHEET (Darpan's sheet of 02-Oct, uploaded to /tmp) is not there - nothing installed"; exit 1; }
fi
say "[1/11] kit gates green (SUMS, KIT_ID part 1, the venv's flask, the earlier walks, the kit's DUTY_MAP.json v4, the databases, the readers)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$(dest "$f")")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: the eleven files are at the kit's pins; $SVC $(systemctl is-active "$SVC") · finance healthz $(health http://127.0.0.1:8106/finance/healthz)"
  exit 0
fi
for f in "${ORDER[@]}"; do
  case " ${NEWF[*]} " in *" $f "*) [ -e "$(dest "$f")" ] && { say "!! [2/11] $(dest "$f") exists already - nothing installed"; exit 1; }; continue;; esac
  [ "$(m5 "$(dest "$f")")" = "${FROM[$f]}" ] || { say "!! [2/11] $(dest "$f") is $(m5 "$(dest "$f")"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }
done
crontab -l 2>/dev/null | grep -qxF "$CRON_OLD" || { say "!! [2/11] the crontab's order_rules line is not the one S410 wrote - nothing installed"; exit 1; }
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
say "[2/11] the eight live files at their FROM pins, the three new ones absent, the cron line as S410 wrote it"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s454p1.py --finance "$FIN" --marg "$MRG" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ -s "$WALK/built/$f" ] || { say "!! [3/11] the build wrote no $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
if [ "${DRY:-0}" = 1 ] && [ "${NOPIN:-0}" = 1 ]; then
  for f in "${ORDER[@]}"; do say "   built $f $(m5 "$WALK/built/$f")"; done
else
  for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/11] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
  say "[3/11] live bytes + anchored edits give exactly the kit's files (eleven pins match)"
fi
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do case "$f" in *.py) cp -p "$WALK/built/$f" "$WALK/cc/built_$f";; esac; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/11] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import json,sys; json.load(open(sys.argv[1],encoding='utf-8'))" "$WALK/built/signatures.json" || { say "!! [4/11] the built signatures.json does not parse - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/11] compiles on /usr/bin/python3 and the venv python (in a scratch copy); signatures.json parses"
R="$WALK/run"
mkdir -p "$R/fin_new/finance_ui" "$R/fin_new/spine" "$R/fin_old/finance_ui" "$R/fin_old/spine" "$R/por" "$R/ast" "$R/shared" "$R/marg_new" "$R/marg_old" "$R/pictures" || exit 1
for side in fin_new fin_old; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
done
for f in "${ORDER[@]}"; do case "$f" in marg_take.py|signatures.json) cp -p "$WALK/built/$f" "$R/marg_new/$f";; *) cp -p "$WALK/built/$f" "$R/fin_new/$f";; esac; done
for side in marg_new marg_old; do
  for f in "$MRG"/*.py "$MRG"/signatures.json; do [ -e "$R/$side/$(basename "$f")" ] || cp -p "$f" "$R/$side/"; done
  cp -rp "$MRG/xlrd" "$R/$side/" 2>/dev/null; cp -rp "$MRG/lib" "$R/$side/" 2>/dev/null
done
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"; cp -p "$SHR"/*.py "$R/shared/" 2>/dev/null; cp -p "$AST"/*.py "$AST"/*.js "$R/ast/" 2>/dev/null
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/spine.db" || { say "!! [5/11] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s454p1.py" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --marg-new "$R/marg_new" --marg-old "$R/marg_old" \
         --por "$R/por" --ast "$R/ast" --shared "$R/shared" --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/spine.db" --kit "$KDIR" --duty-map "$DUTYMAP" \
         --uploads "$AST/uploads" --reader-new "$KDIR/medical/marg_txt.py" --reader-old "$KITS/S446_AMIR_STAGES_BILLS/medical/marg_txt.py" 2>&1 )"
echo "$WOUT" | mask | cut -c1-700 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S454P1 GREEN" || { say "!! [5/11] walk_s454p1 red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/11] walk_s454p1 green on scratch copies of finance.db, assets.db and the spine (the sheet, the screen, the tie, the staff-eye walk), its negative control red on the box as it is (above)"
O="$WALK/old"; mkdir -p "$O" || exit 1
"$VPY" -B plan_old_s454p1.py --work "$O" --fin-new "$R/fin_new" --fin-old "$R/fin_old" --ast "$AST" --por "$POR" --shared "$SHR" --kits "$KITS" --db "$DBF" --adb "$ADB" \
  --spine "$SPD" --duty-map-old "$DUTYMAP_OLD" --duty-map "$DUTYMAP" --py "$VPY" --out "$O/plan.json" | sed 's/^/   /'
OOUT="$( cd "$O" && timeout 7000 "$VPY" -B "$KDIR/walks_old_s454p1.py" --plan "$O/plan.json" 2>&1 )"
echo "$OOUT" | mask | cut -c1-800 | sed 's/^/   /'
echo "$OOUT" | grep -q "^WALKS_OLD_S454P1 GREEN" || { say "!! [6/11] an earlier walk is red on the patched files beyond its named reds - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/11] re-run on the patched files: the twelve earlier walks -- green but for the named reds, each red on the box as it is too"
if [ "${DRY:-0}" = 1 ]; then
  say "-- DRY RUN: every gate, the build and every walk green; NOTHING placed, nothing restarted"; rm -rf "$WALK"; exit 0
fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/11] the build lock $LOCK is not held by $KIT - nothing installed (CLAUDE.md: one build at a time)"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  case " ${NEWF[*]} " in *" $f "*) [ -e "$(dest "$f")" ] && { say "!! [7/11] $(dest "$f") appeared during the walks - nothing installed"; rm -rf "$WALK"; exit 1; }; continue;; esac
  [ "$(m5 "$(dest "$f")")" = "${FROM[$f]}" ] || { say "!! [7/11] $(dest "$f") moved during the walks - nothing installed"; rm -rf "$WALK"; exit 1; }
done
copydb "$DBF" "$FIN/finance.db.bak_S454_$STAMP" || { say "!! [7/11] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
crontab -l > "$FIN/crontab.bak_S454_$STAMP" || { say "!! [7/11] crontab backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  case " ${NEWF[*]} " in *" $f "*) continue;; esac
  BAK[$f]="$(dest "$f").bak_S454_$(m5 "$(dest "$f")" | cut -c1-8)"; \cp -p "$(dest "$f")" "${BAK[$f]}" || { say "!! [7/11] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[7/11] finance.db.bak_S454_$STAMP made (backup API); crontab.bak_S454_$STAMP; .bak_S454_<from8> beside the eight files; the lock is held by $KIT"
restore() {
  say "!! RED after placing ($1) - restoring the files byte-identically"
  for f in "${ORDER[@]}"; do
    case " ${NEWF[*]} " in *" $f "*) rm -f "$(dest "$f")"; continue;; esac
    \cp -p "${BAK[$f]}" "$(dest "$f")"
  done
  crontab "$FIN/crontab.bak_S454_$STAMP" || true
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $(dest "$f") $(m5 "$(dest "$f")")"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · crontab restored · the database backup stays: $FIN/finance.db.bak_S454_$STAMP"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp "$WALK/built/$f" "$(dest "$f")" || restore "copy"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$(dest "$f")")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
crontab -l | awk -v old="$CRON_OLD" -v new="$CRON_NEW" '{ if ($0 == old) print new; else print }' | crontab - || restore "crontab"
crontab -l | grep -qxF "$CRON_NEW" && ! crontab -l | grep -qxF "$CRON_OLD" || restore "crontab read-back"
[ "$(crontab -l | wc -l)" = "$(wc -l < "$FIN/crontab.bak_S454_$STAMP")" ] || restore "crontab line count"
say "[8/11] placed; all eleven md5s read back = the kit's pins; the order_rules cron line now runs every ten minutes, 05:00-21:50 (one line changed)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart $SVC"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); c2=$(health http://127.0.0.1:8106/finance/porders); c3=$(health http://127.0.0.1:8106/finance/porders/s454/order)
c4=$(health http://127.0.0.1:8106/finance/darpan/kal); c5=$(health http://127.0.0.1:8106/finance/purchase/page/scans); c6=$(health http://127.0.0.1:8106/finance/porders/s454/sheet.pdf)
say "health : finance healthz $c1 · /finance/porders $c2 · Order karna hai $c3 · Darpan's Kal ka hisaab $c4 · Scan links $c5 · the order sheet PDF $c6 (302/401 = the login gate, expected)"
gate() { [ "$1" = 302 ] || [ "$1" = 401 ]; }
[ "$c1" = 200 ] && gate "$c2" && gate "$c3" && gate "$c4" && gate "$c5" && gate "$c6" || restore "finance health"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
JR="$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "$JR" = 0 ] || { journalctl -u "$SVC" --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "$SVC journal: $JR error line(s)"; }
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
say "[9/11] $SVC active; healthz 200; the pages behind their gates; nothing 'NOT mounted'; no traceback; finance_app/portal/tile_grants/approvals/packs/asset_register/... untouched"
AOUT="$( cd "$FIN" && FINANCE_DB="$DBF" MARG_INGEST_DIR="$MRG" "$VPY" -B "$KDIR/first_load_s454.py" --db "$DBF" --finance "$FIN" --marg "$MRG" --reader "$KDIR/medical/marg_txt.py" \
         --sheet "$SHEET" 2>&1 )" || { echo "$AOUT" | mask | tail -20; restore "the first load"; }
echo "$AOUT" | mask | sed 's/^/   /'
echo "$AOUT" | grep -q "^S454 first load done" || restore "the first load"
TOUT="$( cd "$FIN" && FINANCE_DB="$DBF" MARG_INGEST_DIR="$MRG" "$VPY" -B - "$FIN" "$DBF" <<'PYEOF' 2>&1
import sqlite3, sys
sys.path.insert(0, sys.argv[1])
import order_sheet
con = sqlite3.connect(sys.argv[2], timeout=60)
con.row_factory = sqlite3.Row
print("S454 first pass: %s" % order_sheet.cron_pass(con, "S454 install"))
PYEOF
)"
echo "$TOUT" | mask | tail -3 | cut -c1-600 | sed 's/^/   /'
echo "$TOUT" | grep -q "^S454 first pass:" || restore "the first pass"
say "[10/11] the first load ran on the live database (above): Darpan's sheet of 02-Oct, as already ordered; then one pass of the tie and Marg's clearing (no notice sent)"
"$VPY" -B - "$DBF" "$DUTYMAP" <<'PYEOF' | mask | sed 's/^/   /'
import json, sqlite3, sys
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
dm = json.load(open(sys.argv[2], encoding="utf-8"))
for d in dm["duties"]:
    if d["id"] in ("reception.medicine_orders", "reception.order_arrival", "reception.bill_scan", "reception.scan_questions", "darpan.order_sheet", "shavez.supplier_messages"):
        try:
            r = con.execute(d["due_sql"]).fetchone()
            print("due_sql %-27s n=%s since=%s" % (d["id"], r[0], r[1]))
        except Exception as e:
            print("due_sql %-27s ERROR %s" % (d["id"], str(e)[:120]))
for r in con.execute("SELECT o.id, o.vendor, o.status, t.stamp FROM purchase_order o LEFT JOIN order_scan_tie t ON t.order_id=o.id WHERE o.order_via='paper' ORDER BY o.vendor"):
    print("paper order #%d %-34s %-9s %s" % (r[0], r[1], r[2], ("arrived by the scan " + r[3]) if r[3] else "awaited"))
PYEOF
c1=$(health http://127.0.0.1:8106/finance/healthz)
[ "$c1" = 200 ] || restore "finance healthz after the data step"
for f in "${ORDER[@]}"; do md5sum "$(dest "$f")"; done
rm -rf "$WALK"
say "[11/11] the six duty-map queries read on the live database (above, read only); healthz $c1"
say "$KIT part 1: DONE -- https://followup.dr-manoj.in/finance/porders · https://followup.dr-manoj.in/finance/porders?old=1 (the owner's cards and settings)"
