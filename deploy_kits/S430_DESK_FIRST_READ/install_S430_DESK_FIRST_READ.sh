#!/bin/bash
# =============================================================================
#  install_S430_DESK_FIRST_READ.sh · kit S430_DESK_FIRST_READ (session 283, 27-Sep-2026, D637, F-650) · Sanjeevni
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S430_DESK_FIRST_READ/install_S430_DESK_FIRST_READ.sh
#  (DRY=1 runs every gate, the build and every walk, and places nothing. KITS=<dir> names the folder holding the S410/S414 kits
#   when this kit is run from a copy.)
#
#  WHAT THE OWNER FOUND ON THE FIRST LIVE READ (runs after S428): Owner's use (a fifth destination, a recorded non-loss); the
#  consumption list gains Vinbactum DS and the two Vintaz P spellings (joined); Old stock (never a Big loss); the one Close button at
#  the top too; F-650: leakage dated by count period; the watch list without dead orthotics; count-#1 traces read 'first count';
#  the four 'units' hints of order_rules.py in strips / pcs.
#
#  PATCHED ON THE BOX from the live bytes (make_s430.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/stock_loss.html    29809ba1 -> see TO   the fifth destination, the pile's two groups, the top Close button, the headers
#          /root/finance/stock_amir.html    e5e22927 -> see TO   the owner's-use round label
#          /root/finance/order_rules.py     b17226d4 -> see TO   the four hints through qty_words
#  REPLACED (whole file, shipped in the kit):  /root/finance/loss_piles.py  9dc06c90 -> see TO (v2.1)
#                                              /root/finance/stock_watch.py ec399909 -> see TO (v1.1)
#  DATA: seed_s430.py on the live database after the backup and a green restart -- the owner's words as data (owner's use moves,
#  the list, the Vintaz alias, the settings, the traces re-labelled). Restarts clinic-finance ONLY. The walk (this kit's, with its
#  negative control), then S427's and S428's walks with the named adjustments (walk_s427_s430 / walk_s428_s430, in this kit), then
#  S414's and S410's walks (order_rules.py) re-run on the patched files.
# =============================================================================
set -u
KIT="S430_DESK_FIRST_READ"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
K410="$(cd "$KITS/S410_MEDICINE_ORDERING" 2>/dev/null && pwd)"
K414="$(cd "$KITS/S414_RULES_PAGE_UX" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPDB="$FIN/spine/spine.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s430_walk_$STAMP"
declare -A FROM=( [stock_loss.html]=29809ba1e3ce415fc43f5df614f7ea0e [stock_amir.html]=e5e229270de7a71a624505bfd0ca11b7
                  [order_rules.py]=b17226d4cc10d7cf9fef8a75465ac76b [loss_piles.py]=9dc06c9000539b6fbf3f77ddac967c7d
                  [stock_watch.py]=ec3999093387d979b754276b9911929d )
declare -A TO=( [stock_loss.html]=ab60c341336c8c897699db18e830211d [stock_amir.html]=3cf1f73ee707a2d3cff6781ba4c36012 [order_rules.py]=00a60efb515972313839662ff7f83495
                [loss_piles.py]=3720b2e1261fd83932b07e2a319a0687 [stock_watch.py]=6a51e47b891b717fbb51b030d4a29f02 )
PATCHED=(stock_loss.html stock_amir.html order_rules.py)
ALLF=("${PATCHED[@]}" loss_piles.py stock_watch.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K410" "$K414" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K410/walk_s410.py" "$K410/seed_s410.py" "$K414/walk_s414.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS) - the earlier walks re-run; nothing installed"; exit 1; }
done
"$VPY" -c "import pywebpush, flask, pypdf, openpyxl" 2>/dev/null || { say "!! [1/10] the venv python lacks pywebpush / flask / pypdf / openpyxl (the walks need them); nothing installed"; exit 1; }
[ -f "$SPDB" ] || { say "!! [1/10] the spine $SPDB is not there; nothing installed"; exit 1; }
say "[1/10] kit gates green (SUMS, KIT_ID, the S410/S414 walks found, the venv modules, the spine)"
ALL=1; for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the five files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance); healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"; exit 0; fi
for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] the five live files at their FROM pins"
S428_BAK="$FIN/finance.db.bak_S428_20260927_103804"     # the database as S428's install found it (10:38 IST) -- S427's frozen walk still sees the three parked lines there (declared)
[ -f "$S428_BAK" ] || { say "!! [2/10] $S428_BAK is not there (S427's walk re-runs on it); nothing installed"; exit 1; }
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" "$WALK/old414/finance_ui" "$WALK/old414/spine" \
         "$WALK/old427/finance_ui" "$WALK/old427/spine" "$WALK/old428/finance_ui" "$WALK/old428/spine" \
         "$WALK/old410/finance_ui" "$WALK/old410/spine" "$WALK/uploads" "$WALK/stub" "$WALK/fig" || exit 1
"$SPY" -B make_s430.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
cp -p "$KDIR/loss_piles.py" "$KDIR/stock_watch.py" "$WALK/built/"
for f in "${ALLF[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/10] live bytes + anchored edits give exactly the kit's files (five pins match)"
( "$SPY" -m py_compile make_s430.py walk_s430.py walk_s427_s430.py walk_s428_s430.py seed_s430.py figures_s430.py "$WALK/built/loss_piles.py" "$WALK/built/stock_watch.py" "$WALK/built/order_rules.py" 2>/dev/null \
  && "$VPY" -m py_compile walk_s430.py walk_s427_s430.py walk_s428_s430.py seed_s430.py figures_s430.py "$WALK/built/loss_piles.py" "$WALK/built/stock_watch.py" "$WALK/built/order_rules.py" 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in finance old old414 old427 old428 old410; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
  cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$FIN/spine/spine.db" "$WALK/$side/spine/" 2>/dev/null
done
for f in "${ALLF[@]}"; do cp -p "$WALK/built/$f" "$WALK/finance/$f"; done
# old427 = before S427 (S427's own negative control): its seven .bak_S427 files, no qty_words / stock_watch
for pair in "stock_app.py:cf464882" "stock_hub.html:bb8741fa" "stockmatch.py:d5f9392f" "stockmatch.html:9a090e03" "stock_amir.html:c2ea41b2" "loss_piles.py:3b6554f8" "stock_loss.html:16cdddaa"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S427_$h" "$WALK/old427/$f" || { say "!! [5/10] $f.bak_S427_$h missing - cannot rebuild the pre-S427 control"; rm -rf "$WALK"; exit 1; }
done
rm -f "$WALK/old427/qty_words.py" "$WALK/old427/stock_watch.py"
# old428 = before S428 (S428's own negative control): its eight .bak_S428 files, no stock_watch
for pair in "stock_app.py:24c2b5fe" "stockmatch.py:e85807da" "stockmatch.html:ecd039f4" "stock_amir.html:244ac6ee" "stock_loss.html:fdd913e7" "sanjeevni_approvals.py:64548b9b" "packs_checklist.html:6f027a7e"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S428_$h" "$WALK/old428/$f" || { say "!! [5/10] $f.bak_S428_$h missing - cannot rebuild the pre-S428 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S428_588975fc" "$WALK/old428/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old428/stock_watch.py"
# the S427 / S428 walks import their seeds from beside themselves: the kits' seeds, copied next to the adjusted walks
cp -p "$KITS/S427_LOSS_DESK_RULINGS/seed_s427.py" "$KITS/S428_STOCK_WATCH/seed_s428.py" "$WALK/" || { say "!! [5/10] the S427/S428 seeds must be reachable (KITS=$KITS)"; rm -rf "$WALK"; exit 1; }
cp -p "$KDIR/walk_s427_s430.py" "$KDIR/walk_s428_s430.py" "$KDIR/walk_s430.py" "$KDIR/seed_s430.py" "$WALK/"
# old414 = before S414 (S414's own negative control): its two .bak_S414 files
cp -p "$FIN/order_rules.py.bak_S414_df6196fc" "$WALK/old414/order_rules.py" || { say "!! [5/10] order_rules.py.bak_S414_df6196fc missing - cannot rebuild the pre-S414 control"; rm -rf "$WALK"; exit 1; }
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S414_7de58315" "$WALK/old414/finance_ui/finance_approvals.html" || { say "!! [5/10] finance_approvals.html.bak_S414_7de58315 missing"; rm -rf "$WALK"; exit 1; }
# old410 = before S410 (S410's own negative control), as S414's installer rebuilt it
for pair in "porders.py:d08f59e2" "porders.html:76a173af" "sanjeevni_approvals.py:3cde91fb" "darpan_kal.py:401ee01c" "darpan_kal.html:1bedb469"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S410_$h" "$WALK/old410/$f" || { say "!! [5/10] $f.bak_S410_$h missing - cannot rebuild the pre-S410 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S410_77c79211" "$WALK/old410/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old410/order_rules.py"
copydb "$DBF" "$WALK/scratch1.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
for i in 428 414 410; do copydb "$DBF" "$WALK/scratch$i.db" || { rm -rf "$WALK"; exit 1; }; done
copydb "$S428_BAK" "$WALK/scratch427.db" || { say "!! [5/10] no scratch copy of $S428_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$SPDB" "$WALK/spine_scratch.db" || { say "!! [5/10] no scratch copy of the spine - nothing installed"; rm -rf "$WALK"; exit 1; }
for i in 427 428; do copydb "$SPDB" "$WALK/spine_scratch$i.db" || { rm -rf "$WALK"; exit 1; }; done
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" SPINE_DB="$WALK/spine_scratch.db" timeout 2400 "$VPY" -B "$WALK/walk_s430.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" --spine "$WALK/spine_scratch.db" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S430 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s430 green on scratch copies of the live database and the spine, its negative control red on the box as it is (above)"
W427="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch427.db" SPINE_DB="$WALK/spine_scratch427.db" timeout 2400 "$VPY" -B "$WALK/walk_s427_s430.py" --app "$WALK/finance" --old "$WALK/old427" --db "$WALK/scratch427.db" --spine "$WALK/spine_scratch427.db" 2>&1 )"
echo "$W427" | grep -E '^(WALK_S427|  FAIL|-- )' | sed 's/^/   /'
echo "$W427" | grep -q "^WALK_S427 GREEN" || { say "!! [6/10] S427's walk (S430 adjustments) went red - nothing installed"; echo "$W427" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W428="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch428.db" SPINE_DB="$WALK/spine_scratch428.db" timeout 2400 "$VPY" -B "$WALK/walk_s428_s430.py" --app "$WALK/finance" --old "$WALK/old428" --db "$WALK/scratch428.db" --spine "$WALK/spine_scratch428.db" 2>&1 )"
echo "$W428" | grep -E '^(WALK_S428|  FAIL|-- )' | sed 's/^/   /'
echo "$W428" | grep -q "^WALK_S428 GREEN" || { say "!! [6/10] S428's walk (S430 adjustment) went red - nothing installed"; echo "$W428" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W414="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch414.db" SPINE_DB="$WALK/spine_scratch.db" timeout 900 "$VPY" -B "$K414/walk_s414.py" --app "$WALK/finance" --old "$WALK/old414" --db "$WALK/scratch414.db" 2>&1 )"
echo "$W414" | grep -E '^(WALK_S414|  FAIL|-- )' | sed 's/^/   /'
echo "$W414" | grep -q "^WALK_S414 GREEN" || { say "!! [6/10] S414's walk went red on the patched order_rules.py - nothing installed"; echo "$W414" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W410="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch410.db" SPINE_DB="$WALK/spine_scratch.db" timeout 900 "$VPY" -B "$K410/walk_s410.py" --app "$WALK/finance" --old "$WALK/old410" --db "$WALK/scratch410.db" 2>&1 )"
echo "$W410" | grep -E '^(WALK_S410|  FAIL|-- )' | sed 's/^/   /'
echo "$W410" | grep -q "^WALK_S410 GREEN" || { say "!! [6/10] S410's walk went red on the patched order_rules.py - nothing installed"; echo "$W410" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S427's walk (on the 10:38 backup of 27-Sep, its pre-S427 control) and S428's walk (its pre-S428 control) with the named S430 adjustments, S414's and S410's walks re-run on the patched files: green (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the build and every walk green; NOTHING placed, nothing restarted"; rm -rf "$WALK"; exit 0; fi
copydb "$DBF" "$FIN/finance.db.bak_S430_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ALLF[@]}"; do BAK[$f]="$FIN/$f.bak_S430_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S430_$STAMP made (backup API); .bak_S430_<from8> beside the five files"
restore() {
  say "!! RED after placing - restoring the five files byte-identically"
  for f in "${ALLF[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart clinic-finance || true; sleep 5
  for f in "${ALLF[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S430_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ALLF[@]}"; do \cp -p "$WALK/built/$f" "$FIN/$f" || restore; done
for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[8/10] placed; all five md5s read back = the kit's pins"
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/stock/page/loss?count=1")
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/porders)
say "health : finance healthz $c2 · /finance/stock/page/loss $c3 · /finance/porders $c4 without a login (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[9/10] clinic-finance active, healthz 200, the desk behind its login gate, nothing 'NOT mounted'"
SOUT="$( cd /tmp && "$SPY" -B "$KDIR/seed_s430.py" --app "$FIN" --db "$DBF" 2>&1 )" || { echo "$SOUT" | tail -20; restore; }
echo "$SOUT" | sed 's/^/   /'
copydb "$DBF" "$WALK/fig/scratch_fig.db" && ( cd "$WALK/fig" && env FINANCE_SSO_DIR=$POR timeout 900 "$SPY" -B "$KDIR/figures_s430.py" --app "$WALK/finance" --db "$WALK/fig/scratch_fig.db" 2>&1 ) | sed 's/^/   /'
say "[10/10] the owner's words seeded on the live database (owner's use, the list, the alias, the settings, the traces); the desk after S430 (above, read on a fresh scratch copy)"
clean; rm -rf "$WALK"
for f in "${ALLF[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/stock/page/loss?count=1"
