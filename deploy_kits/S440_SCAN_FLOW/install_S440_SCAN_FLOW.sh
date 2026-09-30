#!/bin/bash
# =============================================================================
#  install_S440_SCAN_FLOW.sh · kit S440_SCAN_FLOW (session 283, 30-Sep-2026, D640 · F-662) · Sanjeevni + the asset app (PARENT'S, declared)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S440_SCAN_FLOW/install_S440_SCAN_FLOW.sh
#  (DRY=1 runs every gate, the build and every walk, then shows on fresh scratch copies what reception WOULD see, and places nothing.
#   KITS=<dir> names the folder holding the S403 / S409 / S435 / S439 kits when this kit is run from a copy. NOPIN=1, with DRY=1 only,
#   prints the built md5s instead of refusing on a TO mismatch.)
#
#  THE OWNER, 30-Sep: "Whatever needs to be done should be clearly mentioned in the staff scan app ... a back-to-top float on long pages,
#  a prominent BACK button at the top for good navigation, and easy flow. I need this system working properly to shift to it."
#   * Purchase orders, section 3 is "Scan ka kaam (N)": Scan karo · Yahi bill hai? · Supplier chuno · Amount milao · Marg ka intezaar --
#     every line a person must decide carries its own buttons; the answers are kept in purchase_scan_state and ride every pass.
#   * A sticky "← BACK" bar and a floating up-arrow on Purchase orders, the owner's Scan links, and the asset app's intake, slip,
#     Purchases list, bill page and Scan lanes. A scanning login sees that bar instead of the register's menu.
#   * The intake is camera-first; the slip is the Save card; a scanning login has its own read-only list in staff words.
#
#  PATCHED ON THE BOX from the live bytes (make_s440.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/porders.py            64465af0 -> see TO   the S440 block appended (porders_block_s440.py); 5 anchored edits
#          /root/finance/porders.html          124c4d41 -> see TO   the bar, the up-arrow, section 3
#          /root/finance/purchase_app.py       ebe38c68 -> see TO   the matcher keeps a person's decisions; the Scan links page
#          /root/assetapp/asset_register.py    1f80773b -> see TO   PARENT'S, declared in the brief (asset_block_s440.py + anchored edits)
#  DATA:   additive columns on purchase_scan_state (finance.db, backed up first), made by the first pass after the restart.
#          assets.db (backed up first): no schema change; "Galat lane" writes what the S409 re-lane already writes.
#  Restarts clinic-finance AND assetapp. The walk (this kit's, with its negative control on the box as it is), then S439's walk,
#  S403's walk and S435's walk UNCHANGED, and S409's walk with two named assertions adjusted (walk_s409_s440.py).
# =============================================================================
set -u
KIT="S440_SCAN_FLOW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
K403="$(cd "$KITS/S403_PURCHASE_ORDERS_LIVE" 2>/dev/null && pwd)"
K409="$(cd "$KITS/S409_SCAN_LANES" 2>/dev/null && pwd)"
K435="$(cd "$KITS/S435_SCAN_BILL_MONTH" 2>/dev/null && pwd)"
K439="$(cd "$KITS/S439_SCANS_SMS_SCROLL" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPDB="$FIN/spine/spine.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s440_walk_$STAMP"
declare -A FROM=( [porders.py]=64465af0835bdc5583ae7468cacc8c16 [porders.html]=124c4d41b9491203899f324b8a194763
                  [purchase_app.py]=ebe38c681f323782f0a211d1d0879b24 [asset_register.py]=1f80773b85583d0f9e3344b74b313389 )
declare -A TO=( [porders.py]=e43adfb03f11b1b658805553b8441ae5 [porders.html]=792aebbacc377198f7081b6129429f6f [purchase_app.py]=a51fe90eaa2922ba4e2b4db6388f797a [asset_register.py]=0deaa531a412979d523ae0d4fd000946 )
declare -A DIR=( [porders.py]="$FIN" [porders.html]="$FIN" [purchase_app.py]="$FIN" [asset_register.py]="$AST" )
ORDER=(porders.py porders.html purchase_app.py asset_register.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K403" "$K409" "$K435" "$K439" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K403/walk_s403.py" "$K403/seed_s403.py" "$K409/walk_s409.py" "$K409/seed_s409.py" "$K435/walk_s435.py" "$K439/walk_s439.py" "$K439/replay_s439.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS) - the earlier walks re-run; nothing installed"; exit 1; }
done
"$VPY" -c "import pywebpush, flask, pypdf, openpyxl" 2>/dev/null || { say "!! [1/10] the venv python lacks pywebpush / flask / pypdf / openpyxl (the walks need them); nothing installed"; exit 1; }
command -v convert >/dev/null && command -v pdftoppm >/dev/null || { say "!! [1/10] ImageMagick's convert / pdftoppm are not there (the thumbnail and the walks need them); nothing installed"; exit 1; }
[ -f "$ADB" ] || { say "!! [1/10] $ADB is not there; nothing installed"; exit 1; }
say "[1/10] kit gates green (SUMS, KIT_ID, the S403 / S409 / S435 / S439 walks found, the venv modules, convert + pdftoppm, assets.db)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the four files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance) · assetapp $(systemctl is-active assetapp) · healthz $(health http://127.0.0.1:8106/finance/healthz)"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] ${DIR[$f]}/$f is $(m5 "${DIR[$f]}/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] the four live files at their FROM pins"
# The scratch databases of the earlier walks, as S439 declared them: S403's frozen walk needs the finance backup of 26-Sep 17:45 and the
# assets backup of 28-Sep 10:37 (on today's data it is red on the unpatched files too -- every YUVIKA bill of September now has a scan).
S414_BAK="$FIN/finance.db.bak_S414_20260926_174505"
A435_BAK="$AST/assets.db.bak_S435_20260928_103702"
# S439's frozen walk asserts, as its negative control, that the OLD SMS door keeps no field names (no bank_sms_ignored.fields column) --
# a column S439's own install added to the live database. Its finance scratch is therefore a copy of the backup S439 took before placing.
S439_BAK="$(ls -1 "$FIN"/finance.db.bak_S439_* 2>/dev/null | tail -1)"
for b in "$S414_BAK" "$A435_BAK" "${S439_BAK:-$FIN/finance.db.bak_S439_}"; do [ -f "$b" ] || { say "!! [2/10] $b is not there (an earlier walk re-runs on it); nothing installed"; exit 1; }; done
SIDES="finance old old403 old409 old439"
for s in $SIDES; do mkdir -p "$WALK/$s/finance_ui" "$WALK/$s/spine" || exit 1; done
mkdir -p "$WALK/built" "$WALK/assetapp_new" "$WALK/assetapp_live" "$WALK/assetapp_old3" "$WALK/assetapp_old9" "$WALK/p408" "$WALK/p403" "$WALK/uploads" "$WALK/stub" "$WALK/fig" "$WALK/w409" "$WALK/w435" || exit 1
"$SPY" -B make_s440.py --finance "$FIN" --assetapp "$AST" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ -s "$WALK/built/$f" ] || { say "!! [3/10] the build wrote no $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
if [ "${DRY:-0}" = 1 ] && [ "${NOPIN:-0}" = 1 ]; then
  for f in "${ORDER[@]}"; do say "   built $f $(m5 "$WALK/built/$f")"; done
else
  for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
  say "[3/10] live bytes + anchored edits give exactly the kit's files (four pins match)"
fi
PYS="make_s440.py walk_s440.py walk_s409_s440.py figures_s440.py $WALK/built/porders.py $WALK/built/purchase_app.py $WALK/built/asset_register.py"
( "$SPY" -m py_compile $PYS 2>/dev/null && "$VPY" -m py_compile $PYS 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in $SIDES; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
  cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null
  [ -f "$SPDB" ] && cp -p "$SPDB" "$WALK/$side/spine/"
done
for f in porders.py porders.html purchase_app.py; do cp -p "$WALK/built/$f" "$WALK/finance/$f"; done
# old403 = before S403 (S403's own negative control), as every kit since S403 rebuilt it
for pair in "purchase_app.py:9ad50878" "darpan_kal.py:1958ee7c" "darpan_kal.html:4f115f44" "sale_check.py:92ca5cb2" "sale_check.html:9c70af26" "sanjeevni_approvals.py:5fdfa364" "finance_app.py:186a500a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S403_$h" "$WALK/old403/$f" || { say "!! [5/10] $f.bak_S403_$h missing - cannot rebuild the pre-S403 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S403_6622587e" "$WALK/old403/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old403/porders.py" "$WALK/old403/porders.html"
# old409 = before S409 (S409's own negative control)
for pair in "purchase_app.py:fdec7ec0" "porders.py:78d1712a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S409_$h" "$WALK/old409/$f" || { say "!! [5/10] $f.bak_S409_$h missing - cannot rebuild the pre-S409 control"; rm -rf "$WALK"; exit 1; }
done
# old439 = before S439 (S439's own negative control)
for pair in "purchase_app.py:9c40d13e" "bank_sms.py:a70d6d96"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S439_$h" "$WALK/old439/$f" || { say "!! [5/10] $f.bak_S439_$h missing - cannot rebuild the pre-S439 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S439_9d1eddc8" "$WALK/old439/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
for side in assetapp_new assetapp_live assetapp_old3 assetapp_old9; do cp -p "$AST"/*.py "$AST"/*.js "$WALK/$side/" 2>/dev/null; done
cp -p "$WALK/built/asset_register.py" "$WALK/assetapp_new/asset_register.py"
cp -p "$AST/asset_register.py.bak_S403_71bd3277" "$WALK/assetapp_old3/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S403_71bd3277 missing"; rm -rf "$WALK"; exit 1; }
cp -p "$AST/asset_register.py.bak_S409_30b26d28" "$WALK/assetapp_old9/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S409_30b26d28 missing"; rm -rf "$WALK"; exit 1; }
cp -p "$POR"/*.py "$WALK/p408/"; cp -p "$POR/portal.py.bak_S408_968ca602" "$WALK/p408/portal.py"; cp -p "$POR/tile_grants.json.bak_S408_0aadfc52" "$WALK/p408/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$KDIR/walk_s440.py" "$KDIR/walk_s409_s440.py" "$KDIR/figures_s440.py" "$K439/walk_s439.py" "$K439/replay_s439.py" "$WALK/"
for i in 1 409; do copydb "$DBF" "$WALK/scratch$i.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }; done
for i in 1 439 409 435; do copydb "$ADB" "$WALK/assets_scratch$i.db" || { say "!! [5/10] no scratch copy of assets.db - nothing installed"; rm -rf "$WALK"; exit 1; }; done
copydb "$S439_BAK" "$WALK/scratch439.db" || { say "!! [5/10] no scratch copy of $S439_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$S414_BAK" "$WALK/scratch403.db" || { say "!! [5/10] no scratch copy of $S414_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$A435_BAK" "$WALK/assets_scratch403.db" || { say "!! [5/10] no scratch copy of $A435_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
[ -f "$SPDB" ] && { copydb "$SPDB" "$WALK/spine_scratch.db" || { rm -rf "$WALK"; exit 1; }; }
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive SPINE_DB=$WALK/spine_scratch.db"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 1800 "$VPY" -B "$WALK/walk_s440.py" --app "$WALK/finance" --old "$WALK/old" \
         --assets-new "$WALK/assetapp_new" --assets-old "$WALK/assetapp_live" --db "$WALK/scratch1.db" --assets-db "$WALK/assets_scratch1.db" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{10,}/##########/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S440 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s440 green on scratch copies of finance.db and assets.db, its negative control red on the box as it is (above)"
W439="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch439.db" timeout 1800 "$VPY" -B "$WALK/walk_s439.py" --app "$WALK/finance" --old "$WALK/old439" --db "$WALK/scratch439.db" --assets-db "$WALK/assets_scratch439.db" --kit "$WALK" 2>&1 )"
echo "$W439" | grep -E '^(WALK_S439|  FAIL|-- )' | sed -E 's/[0-9]{10,}/##########/g' | sed 's/^/   /'
echo "$W439" | grep -q "^WALK_S439 GREEN" || { say "!! [6/10] S439's walk went red on the patched files - nothing installed"; echo "$W439" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W403="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch403.db" timeout 1500 "$VPY" -B "$K403/walk_s403.py" --app "$WALK/finance" --old "$WALK/old403" \
         --assets-new "$WALK/assetapp_new" --assets-old "$WALK/assetapp_old3" --db "$WALK/scratch403.db" --assets-db "$WALK/assets_scratch403.db" \
         --portal-new "$WALK/p408" --portal-old "$WALK/p403" 2>&1 )"
echo "$W403" | grep -E '^(WALK_S403|  FAIL|-- )' | sed 's/^/   /'
echo "$W403" | grep -q "^WALK_S403 GREEN" || { say "!! [6/10] S403's walk went red on the patched files - nothing installed"; echo "$W403" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W409="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch409.db" timeout 1200 "$VPY" -B "$WALK/walk_s409_s440.py" --k409 "$K409" --work "$WALK/w409" -- \
         --assets-new "$WALK/assetapp_new" --assets-old "$WALK/assetapp_old9" --assets-db "$WALK/assets_scratch409.db" --app "$WALK/finance" --old "$WALK/old409" --db "$WALK/scratch409.db" 2>&1 )"
echo "$W409" | grep -E '^(WALK_S409|  FAIL|-- |  ok   S440-ADJUSTED)' | sed 's/^/   /'
echo "$W409" | grep -q "^WALK_S409 GREEN" || { say "!! [6/10] S409's walk (two assertions adjusted) went red on the patched files - nothing installed"; echo "$W409" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W435="$( cd /tmp && ASSETS_LIVE="$AST" timeout 300 "$SPY" -B "$K435/walk_s435.py" "$WALK/assetapp_new" "$WALK/w435" "$WALK/assets_scratch435.db" 2>&1 )"
echo "$W435" | grep -E '^(WALK |  FAIL)' | sed 's/^/   /'
echo "$W435" | tail -1 | grep -q "^WALK OK" || { say "!! [6/10] S435's walk went red on the patched asset app - nothing installed"; echo "$W435" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] re-run on the patched files, each against its own pre-kit control: S439's walk UNCHANGED (on the finance backup S439 took -- declared above), S403's walk UNCHANGED (on the backups S439 declared), S435's walk UNCHANGED, S409's walk with TWO assertions adjusted and named (A1, A2 in walk_s409_s440.py): green (above)"
if [ "${DRY:-0}" = 1 ]; then
  copydb "$DBF" "$WALK/fig/fin.db" && copydb "$ADB" "$WALK/fig/assets.db" && {
    ( cd "$WALK/finance" && FINANCE_DB="$WALK/fig/fin.db" ASSETS_DB="$WALK/fig/assets.db" REMATCH_WHO="dry run S440" "$VPY" -B "$WALK/finance/purchase_app.py" rematch 2>&1 ) | sed 's/^/   /'
    ( "$VPY" -B "$WALK/figures_s440.py" --app "$WALK/finance" --db "$WALK/fig/fin.db" --assets-db "$WALK/fig/assets.db" 2>&1 ) | sed 's/^/   /'
  }
  say "-- DRY RUN: every gate, the build and every walk green; the pass and the figures above ran on fresh scratch copies through the built files; NOTHING placed, nothing restarted"; clean; rm -rf "$WALK"; exit 0
fi
copydb "$DBF" "$FIN/finance.db.bak_S440_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$ADB" "$AST/assets.db.bak_S440_$STAMP" || { say "!! [7/10] assets.db backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DIR[$f]}/$f.bak_S440_$(m5 "${DIR[$f]}/$f" | cut -c1-8)"; \cp -p "${DIR[$f]}/$f" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S440_$STAMP and assets.db.bak_S440_$STAMP made (backup API); .bak_S440_<from8> beside the four files"
restore() {
  say "!! RED after placing ($1) - restoring the four files byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DIR[$f]}/$f"; done
  systemctl restart clinic-finance || true; systemctl restart assetapp || true; sleep 6
  for f in "${ORDER[@]}"; do say "   ${DIR[$f]}/$f $(m5 "${DIR[$f]}/$f")"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · asset app login $(health http://127.0.0.1:8030/login) · the database backups stay: $FIN/finance.db.bak_S440_$STAMP · $AST/assets.db.bak_S440_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "${DIR[$f]}/$f" || restore "copy"; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || restore "md5 read-back"; done
say "[8/10] placed; all four md5s read back = the kit's pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
systemctl restart assetapp || restore "restart assetapp"
sleep 7
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
systemctl is-active --quiet assetapp || restore "assetapp not active"
c2=$(health http://127.0.0.1:8106/finance/healthz)
c3=$(health http://127.0.0.1:8106/finance/porders)
c4=$(health http://127.0.0.1:8106/finance/purchase/page/scans)
c5=$(health "http://127.0.0.1:8106/finance/porders/api/scan-status?ids=1")
a1=$(health http://127.0.0.1:8030/login)
a2=$(health http://127.0.0.1:8030/intake)
a3=$(health http://127.0.0.1:8030/bills)
a4=$(health http://127.0.0.1:8030/bills/1/thumb)
say "health : finance healthz $c2 · /finance/porders $c3 · /finance/purchase/page/scans $c4 · the read door $c5 without a login (302 = a login gate, expected)"
say "         asset app login page $a1 (200 expected) · /intake $a2 · /bills $a3 · a thumbnail $a4 without a login (302 expected)"
[ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } && { [ "$c5" = 302 ] || [ "$c5" = 401 ]; } || restore "finance health"
[ "$a1" = 200 ] && [ "$a2" = 302 ] && [ "$a3" = 302 ] && [ "$a4" = 302 ] || restore "asset app health"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
JR="$(journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "$JR" = 0 ] || { journalctl -u assetapp --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "assetapp journal: $JR error line(s)"; }
say "[9/10] clinic-finance and assetapp active; healthz 200; the pages behind their login gates; nothing 'NOT mounted'; the asset app's journal clean"
ROUT="$( cd "$FIN" && FINANCE_DB="$DBF" REMATCH_WHO="install S440" "$VPY" -B "$FIN/purchase_app.py" rematch 2>&1 )" || { echo "$ROUT" | tail -20; restore "the first pass"; }
echo "$ROUT" | sed 's/^/   /'
echo "$ROUT" | grep -q "^S439 rematch" || restore "the first pass"
FOUT="$( "$VPY" -B "$KDIR/figures_s440.py" --app "$FIN" --db "$DBF" --assets-db "$ADB" 2>&1 )" || { echo "$FOUT" | tail -20; restore "the figures"; }
echo "$FOUT" | sed 's/^/   /'
echo "$FOUT" | grep -q "^Scan ka kaam (" || restore "the figures"
say "[10/10] the first pass ran on the live database (it made the additive columns and named each scan's likely bill); what reception sees on opening Purchase orders is above"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DIR[$f]}/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/porders · https://assets.dr-manoj.in/intake · https://followup.dr-manoj.in/finance/purchase/page/scans"
