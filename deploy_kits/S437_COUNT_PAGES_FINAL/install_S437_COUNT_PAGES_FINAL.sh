#!/bin/bash
# =============================================================================
#  install_S437_COUNT_PAGES_FINAL.sh · kit S437_COUNT_PAGES_FINAL (session 283, 28-Sep-2026, F-659) · Sanjeevni
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S437_COUNT_PAGES_FINAL/install_S437_COUNT_PAGES_FINAL.sh
#  (DRY=1 runs every gate, the build and every walk, and places nothing. KITS=<dir> names the folder holding the S404/S427/S428/S430/S432/S436
#   kits when this kit is run from a copy. NOPIN=1, with DRY=1 only, prints the built md5s instead of refusing on a TO mismatch.)
#
#  THE THREE COUNT PAGES FINISHED THE OWNER'S WAY (28-Sep 14:2x): Amir's board is the vouchers ONLY -- STOCK ISSUE वाउचर 1..N then STOCK
#  RECEIVE वाउचर 1..M, numbered as he keys them; a line is item (packing) · Marg से → तक · कितना and nothing else; Naam badlo only after the
#  proof is green. The STOCK RECEIVE round BY RULE (F-659): every line where the shelf held more than Marg gets its RECEIVE line at every
#  close and, once, at this install for count #1 (with the 15 earlier write-offs that were on no voucher) -- the hub's pending reads 0.
#  Whole-piece items (the CCM bug): stock.whole_unit_items, seeded "CCM = bottle"; every quantity of such an item reads in its word.
#  Darpan's block and the owner's frozen block as TABLES (Badi kami open, Chhoti kami collapsed, the orthotic rows apart), the record PDF too;
#  Darpan's page ends with the orthotic line; the verdict tail and the status lines are gone.
#
#  REPLACED (whole files, shipped in the kit; FROM pins checked):
#          /root/finance/stock_amir.html   d32f39fa -> see TO   the vouchers only, numbered; Naam badlo gated on the proof
#          /root/finance/stockmatch.html   bdfb25e3 -> see TO   the block as tables, last; the foot cut; the pairs folded
#          /root/finance/loss_piles.py     47d6acb3 -> see TO   v2.4: receive_close, block_tables, the whole-piece setting + candidates
#          /root/finance/qty_words.py      f4c15d7e -> see TO   v1.2: the whole-piece map
#  PATCHED ON THE BOX from the live bytes (make_s437.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/stock_app.py           ec9abc48 -> see TO   vouchers_flat + the line words, _voucher_numbers, the renames gate, the whole-piece load, _qw names its item
#          /root/finance/stock_statement.py     24a040b1 -> see TO   v1.3: "Marg corrected -- on STOCK RECEIVE voucher N"
#          /root/finance/stock_hub.html         7b2ea506 -> see TO   pending 0 says so
#          /root/finance/stock_loss.html        5ead2a32 -> see TO   the frozen block as tables; the whole-piece list on the settings card
#  DATA: seed_s437.py on the live database after a green restart -- the setting seeded, the RECEIVE round by rule for count #1. Restarts
#  clinic-finance ONLY. The walk (this kit's, with its negative control), then S430's, S428's (S432's copy), S427's (this kit's copy: one
#  named adjustment, the settings card's new key), S431's and S432's (S436's copies), S436's (this kit's copy: the S437 adjustments named)
#  and S404's (S436's copy) re-run on the patched files, each against its own pre-kit control.
# =============================================================================
set -u
KIT="S437_COUNT_PAGES_FINAL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
K404="$(cd "$KITS/S404_ORTHO_STOCK_CLOSE" 2>/dev/null && pwd)"
K427="$(cd "$KITS/S427_LOSS_DESK_RULINGS" 2>/dev/null && pwd)"
K428="$(cd "$KITS/S428_STOCK_WATCH" 2>/dev/null && pwd)"
K430="$(cd "$KITS/S430_DESK_FIRST_READ" 2>/dev/null && pwd)"
K432="$(cd "$KITS/S432_DESK_GROUP_FLOW" 2>/dev/null && pwd)"
K436="$(cd "$KITS/S436_STAFF_PAGES_CLEAN" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"
DBF="${FINANCE_DB:-$FIN/finance.db}"; SPDB="$FIN/spine/spine.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s437_walk_$STAMP"
declare -A FROM=( [stock_amir.html]=d32f39fad196c84a2cdf1ef5ca2f2598 [stockmatch.html]=bdfb25e38cbc5a4c71171962089e1ccd [loss_piles.py]=47d6acb35a84f9eb81235cad0de2b915
                  [qty_words.py]=f4c15d7e88c84b14c7686d5b28148877 [stock_app.py]=ec9abc4801599d9acd1ab34f66a21a83 [stock_statement.py]=24a040b1b58a21f043ff92ffce1e2860
                  [stock_hub.html]=7b2ea5065c1b1bf110a4301ccd0384a1 [stock_loss.html]=5ead2a32949ec6e77e95b8645db350e2 )
declare -A TO=( [stock_amir.html]=1ec8663dbbad397fe46f093966352e0a [stockmatch.html]=0dc4d303434d6f87d9e470bccb79f54c [loss_piles.py]=202bfc4e3fd798501c6db95373c2a7d4 [qty_words.py]=706db7ccfa7489fb8d296f663590f107
                [stock_app.py]=4f2625c0a88e450c88e0b23d499d6fa8 [stock_statement.py]=1a4f6c9ecb2546dae954c0414074f406 [stock_hub.html]=a710a98a568227d4b2ba220d792e6a2c [stock_loss.html]=0f0dfed658d05d182811005ebce49df3 )
WHOLE=(stock_amir.html stockmatch.html loss_piles.py qty_words.py)
PATCHED=(stock_app.py stock_statement.py stock_hub.html stock_loss.html)
ALLF=("${WHOLE[@]}" "${PATCHED[@]}")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K404" "$K427" "$K428" "$K430" "$K432" "$K436" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K404/seed_s404.py" "$K427/seed_s427.py" "$K428/seed_s428.py" "$K430/walk_s430.py" "$K430/seed_s430.py" \
         "$K432/seed_s432.py" "$K432/walk_s427_s432.py" "$K432/walk_s428_s432.py" "$K436/seed_s436.py" "$K436/walk_s431_s436.py" "$K436/walk_s432_s436.py" "$K436/walk_s404_s436.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS) - the earlier walks re-run; nothing installed"; exit 1; }
done
"$VPY" -c "import pywebpush, flask, pypdf, openpyxl" 2>/dev/null || { say "!! [1/10] the venv python lacks pywebpush / flask / pypdf / openpyxl (the walks need them); nothing installed"; exit 1; }
[ -f "$SPDB" ] || { say "!! [1/10] the spine $SPDB is not there; nothing installed"; exit 1; }
say "[1/10] kit gates green (SUMS, KIT_ID, the S404/S427/S428/S430/S432/S436 walks found, the venv modules, the spine)"
ALL=1; for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the eight files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance); healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"; exit 0; fi
for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] the eight live files at their FROM pins"
S428_BAK="$FIN/finance.db.bak_S428_20260927_103804"     # S427's walk runs there (the count still open, the parked lines as S427 froze them)
S430_BAK="$FIN/finance.db.bak_S430_20260927_121728"     # S430's and S428's walks run there (before the owner closed the count at 12:58)
S412_BAK="$FIN/finance.db.bak_S412_20260926_140429"     # S404's walk's database, as every kit since S404 re-ran it
S436_BAK="$FIN/finance.db.bak_S436_20260928_130938"     # S436's own walk runs there: the database as it was before S436's seed (the section open)
for b in "$S428_BAK" "$S430_BAK" "$S412_BAK" "$S436_BAK"; do [ -f "$b" ] || { say "!! [2/10] $b is not there (an earlier walk re-runs on it); nothing installed"; exit 1; }; done
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" \
         "$WALK/old430/finance_ui" "$WALK/old430/spine" "$WALK/old427/finance_ui" "$WALK/old427/spine" "$WALK/old428/finance_ui" "$WALK/old428/spine" \
         "$WALK/old431/finance_ui" "$WALK/old431/spine" "$WALK/old432/finance_ui" "$WALK/old432/spine" "$WALK/old436/finance_ui" "$WALK/old436/spine" "$WALK/old404/finance_ui" "$WALK/old404/spine" \
         "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/p403" "$WALK/p404" "$WALK/uploads" "$WALK/stub" "$WALK/fig" || exit 1
"$SPY" -B make_s437.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${WHOLE[@]}"; do cp -p "$KDIR/$f" "$WALK/built/$f"; done
if [ "${DRY:-0}" = 1 ] && [ "${NOPIN:-0}" = 1 ]; then
  for f in "${ALLF[@]}"; do say "   built $f $(m5 "$WALK/built/$f")"; done
else
  for f in "${ALLF[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
  say "[3/10] live bytes + anchored edits + the kit's whole files give exactly the kit's files (eight pins match)"
fi
PYS="make_s437.py walk_s437.py walk_s436_s437.py seed_s437.py figures_s437.py $WALK/built/stock_app.py $WALK/built/stock_statement.py $WALK/built/loss_piles.py $WALK/built/qty_words.py"
( "$SPY" -m py_compile $PYS 2>/dev/null && "$VPY" -m py_compile $PYS 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in finance old old430 old427 old428 old431 old432 old436 old404; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
  cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$FIN/spine/spine.db" "$WALK/$side/spine/" 2>/dev/null
done
for f in "${ALLF[@]}"; do cp -p "$WALK/built/$f" "$WALK/finance/$f"; done
# old430 = before S430 (S430's own negative control): the pre-S432 stock_app / statement / qty_words (S436's installer adjustment) under S430's five .bak_S430 files
for pair in "stock_app.py:2a95e254" "stock_statement.py:85ec7619" "stock_statement.html:175f4654" "qty_words.py:1e67a3e3"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S432_$h" "$WALK/old430/$f" || { say "!! [5/10] $f.bak_S432_$h missing - cannot rebuild the pre-S430 control"; rm -rf "$WALK"; exit 1; }
done
for pair in "loss_piles.py:9dc06c90" "stock_watch.py:ec399909" "stock_loss.html:29809ba1" "stock_amir.html:e5e22927" "order_rules.py:b17226d4"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S430_$h" "$WALK/old430/$f" || { say "!! [5/10] $f.bak_S430_$h missing - cannot rebuild the pre-S430 control"; rm -rf "$WALK"; exit 1; }
done
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
# old431 = before S431 (S431's own negative control): its three .bak_S431 files, no stock_statement
for pair in "stock_app.py:0e0fc043" "stock_hub.html:74ea0699" "stock_report.html:bd750dc8"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S431_$h" "$WALK/old431/$f" || { say "!! [5/10] $f.bak_S431_$h missing - cannot rebuild the pre-S431 control"; rm -rf "$WALK"; exit 1; }
done
rm -f "$WALK/old431/stock_statement.py" "$WALK/old431/stock_statement.html"
# old432 = before S432 (S432's own negative control): its seven .bak_S432 files
for pair in "loss_piles.py:3720b2e1" "stock_watch.py:6a51e47b" "stock_loss.html:ab60c341" "qty_words.py:1e67a3e3" "stock_app.py:2a95e254" "stock_statement.py:85ec7619" "stock_statement.html:175f4654"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S432_$h" "$WALK/old432/$f" || { say "!! [5/10] $f.bak_S432_$h missing - cannot rebuild the pre-S432 control"; rm -rf "$WALK"; exit 1; }
done
# old436 = before S436 (S436's own negative control): its eight .bak_S436 files
for pair in "stockmatch.py:df5501ea" "stockmatch.html:4ddf0073" "stock_amir.html:3cf1f73e" "loss_piles.py:2501b55a" "stock_watch.py:5114e01f" "stock_app.py:02ad3d6a" "stock_hub.html:38e0537c" "stock_statement.py:05c63235"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S436_$h" "$WALK/old436/$f" || { say "!! [5/10] $f.bak_S436_$h missing - cannot rebuild the pre-S436 control"; rm -rf "$WALK"; exit 1; }
done
# old404 = before S404 (S404's own negative control), as every kit since S404 rebuilt it
for pair in "stock_app.py:1b473fbf" "stock_hub.html:c4f3280b" "stock_amir.html:14024b8d" "section_map.py:b05b0f08" "finance_app.py:d7ee72c5"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S404_$h" "$WALK/old404/$f" || { say "!! [5/10] $f.bak_S404_$h missing - cannot rebuild the pre-S404 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/spine/spine_build.py.bak_S404_1378c87d" "$WALK/old404/spine/spine_build.py" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old404/item_alias.py" "$WALK/old404/stockmatch.py" "$WALK/old404/stockmatch.html" "$WALK/old404/loss_piles.py" "$WALK/old404/qty_words.py" "$WALK/old404/stock_watch.py"
for side in marg_ingest marg_old; do cp -p "$MRG"/*.py "$WALK/$side/" 2>/dev/null; cp -rp "$MRG/xlrd" "$WALK/$side/xlrd" 2>/dev/null; [ -d "$MRG/lib" ] && cp -rp "$MRG/lib" "$WALK/$side/lib"; done
cp -p "$MRG/marg_take.py.bak_S404_75b8056c" "$WALK/marg_old/marg_take.py" || { say "!! [5/10] marg_take.py.bak_S404_75b8056c missing"; rm -rf "$WALK"; exit 1; }
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p404/"; cp -p "$POR/portal.py.bak_S404_592ccf99" "$WALK/p404/portal.py"; cp -p "$POR/tile_grants.json.bak_S404_9231cefa" "$WALK/p404/tile_grants.json"
# the earlier walks import their seeds from beside themselves: the kits' seeds and walks, copied together with this kit's
cp -p "$K427/seed_s427.py" "$K428/seed_s428.py" "$K430/seed_s430.py" "$K430/walk_s430.py" "$WALK/" || { say "!! [5/10] the S427/S428/S430 seeds and walks must be reachable (KITS=$KITS)"; rm -rf "$WALK"; exit 1; }
cp -p "$K432/seed_s432.py" "$K432/walk_s428_s432.py" "$WALK/" || { say "!! [5/10] S432's seed and walks must be reachable (KITS=$KITS)"; rm -rf "$WALK"; exit 1; }
cp -p "$K436/seed_s436.py" "$K436/walk_s431_s436.py" "$K436/walk_s432_s436.py" "$K436/walk_s404_s436.py" "$WALK/" || { say "!! [5/10] S436's seed and walks must be reachable (KITS=$KITS)"; rm -rf "$WALK"; exit 1; }
cp -p "$K404/seed_s404.py" "$WALK/" || { say "!! [5/10] S404's seed must be reachable (KITS=$KITS)"; rm -rf "$WALK"; exit 1; }
cp -p "$KDIR/walk_s437.py" "$KDIR/seed_s437.py" "$KDIR/walk_s436_s437.py" "$KDIR/walk_s427_s437.py" "$WALK/"
copydb "$DBF" "$WALK/scratch1.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$S436_BAK" "$WALK/scratch431.db" || { rm -rf "$WALK"; exit 1; }   # S437 adjustment: S431's walk runs on the database as S436 last ran it green (before S436's seed closed the orthotic section by rule)
copydb "$DBF" "$WALK/scratch432.db" || { rm -rf "$WALK"; exit 1; }
copydb "$S436_BAK" "$WALK/scratch436.db" || { rm -rf "$WALK"; exit 1; }
copydb "$S430_BAK" "$WALK/scratch430.db" || { rm -rf "$WALK"; exit 1; }
copydb "$S430_BAK" "$WALK/scratch428.db" || { rm -rf "$WALK"; exit 1; }
copydb "$S428_BAK" "$WALK/scratch427.db" || { say "!! [5/10] no scratch copy of $S428_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$S412_BAK" "$WALK/scratch404.db" || { say "!! [5/10] no scratch copy of $S412_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
for i in "" 430 427 428 431 432 436 404; do copydb "$SPDB" "$WALK/spine_scratch$i.db" || { say "!! [5/10] no scratch copy of the spine - nothing installed"; rm -rf "$WALK"; exit 1; }; done
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" SPINE_DB="$WALK/spine_scratch.db" timeout 2400 "$VPY" -B "$WALK/walk_s437.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" --spine "$WALK/spine_scratch.db" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S437 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s437 green on scratch copies of the live database and the spine, its negative control red on the box as it is (above)"
W430="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch430.db" SPINE_DB="$WALK/spine_scratch430.db" timeout 2400 "$VPY" -B "$WALK/walk_s430.py" --app "$WALK/finance" --old "$WALK/old430" --db "$WALK/scratch430.db" --spine "$WALK/spine_scratch430.db" 2>&1 )"
echo "$W430" | grep -E '^(WALK_S430|  FAIL|-- )' | sed 's/^/   /'
echo "$W430" | grep -q "^WALK_S430 GREEN" || { say "!! [6/10] S430's walk went red on the patched files - nothing installed"; echo "$W430" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W427="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch427.db" SPINE_DB="$WALK/spine_scratch427.db" timeout 2400 "$VPY" -B "$WALK/walk_s427_s437.py" --app "$WALK/finance" --old "$WALK/old427" --db "$WALK/scratch427.db" --spine "$WALK/spine_scratch427.db" 2>&1 )"
echo "$W427" | grep -E '^(WALK_S427|  FAIL|-- )' | sed 's/^/   /'
echo "$W427" | grep -q "^WALK_S427 GREEN" || { say "!! [6/10] S427's walk (this kit's copy: one named adjustment, the new setting key) went red - nothing installed"; echo "$W427" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W428="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch428.db" SPINE_DB="$WALK/spine_scratch428.db" timeout 2400 "$VPY" -B "$WALK/walk_s428_s432.py" --app "$WALK/finance" --old "$WALK/old428" --db "$WALK/scratch428.db" --spine "$WALK/spine_scratch428.db" 2>&1 )"
echo "$W428" | grep -E '^(WALK_S428|  FAIL|-- )' | sed 's/^/   /'
echo "$W428" | grep -q "^WALK_S428 GREEN" || { say "!! [6/10] S428's walk (the S432 copy) went red - nothing installed"; echo "$W428" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W431="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch431.db" SPINE_DB="$WALK/spine_scratch431.db" timeout 2400 "$VPY" -B "$WALK/walk_s431_s436.py" --app "$WALK/finance" --old "$WALK/old431" --db "$WALK/scratch431.db" --spine "$WALK/spine_scratch431.db" 2>&1 )"
echo "$W431" | grep -E '^(WALK_S431|  FAIL|-- )' | sed 's/^/   /'
echo "$W431" | grep -q "^WALK_S431 GREEN" || { say "!! [6/10] S431's walk (the S436 copy) went red - nothing installed"; echo "$W431" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W432="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch432.db" SPINE_DB="$WALK/spine_scratch432.db" timeout 2400 "$VPY" -B "$WALK/walk_s432_s436.py" --app "$WALK/finance" --old "$WALK/old432" --db "$WALK/scratch432.db" --spine "$WALK/spine_scratch432.db" 2>&1 )"
echo "$W432" | grep -E '^(WALK_S432|  FAIL|-- )' | sed 's/^/   /'
echo "$W432" | grep -q "^WALK_S432 GREEN" || { say "!! [6/10] S432's walk (the S436 copy) went red on the patched files - nothing installed"; echo "$W432" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W436="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch436.db" SPINE_DB="$WALK/spine_scratch436.db" timeout 2400 "$VPY" -B "$WALK/walk_s436_s437.py" --app "$WALK/finance" --old "$WALK/old436" --db "$WALK/scratch436.db" --spine "$WALK/spine_scratch436.db" 2>&1 )"
echo "$W436" | grep -E '^(WALK_S436|  FAIL|-- )' | sed 's/^/   /'
echo "$W436" | grep -q "^WALK_S436 GREEN" || { say "!! [6/10] S436's walk (this kit's copy: the S437 adjustments named) went red - nothing installed"; echo "$W436" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W404="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch404.db" SPINE_DB="$WALK/spine_scratch404.db" timeout 1500 "$VPY" -B "$WALK/walk_s404_s436.py" --app "$WALK/finance" --old "$WALK/old404" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch404.db" --portal-new "$WALK/p403" --portal-old "$WALK/p404" 2>&1 )"
echo "$W404" | grep -E '^(WALK_S404|  FAIL|-- )' | sed 's/^/   /'
echo "$W404" | grep -q "^WALK_S404 GREEN" || { say "!! [6/10] S404's walk (the S436 copy) went red on the patched files - nothing installed"; echo "$W404" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S430's and S428's walks (on the 12:17 backup of 27-Sep), S427's (the 10:38 backup; one named adjustment), S431's and S436's (the 13:09 backup of 28-Sep -- the database before S436's seed closed the orthotic section by rule, as S436 last ran S431's walk green; S436's copy carries the S437 adjustments named), S432's (a copy of the live database) and S404's (the 14:04 backup of 26-Sep) re-run on the patched files, each against its own pre-kit control: green (above)"
if [ "${DRY:-0}" = 1 ]; then
  copydb "$DBF" "$WALK/fig/scratch_fig.db" && ( cd "$WALK/fig" && env FINANCE_SSO_DIR=$POR "$SPY" -B "$KDIR/seed_s437.py" --app "$WALK/finance" --db "$WALK/fig/scratch_fig.db" 2>&1 | sed 's/^/   seed (scratch): /' ; \
      env $WENV FINANCE_DB="$WALK/fig/scratch_fig.db" timeout 900 "$SPY" -B "$KDIR/figures_s437.py" --app "$WALK/finance" --db "$WALK/fig/scratch_fig.db" 2>&1 ) | sed 's/^/   /'
  say "-- DRY RUN: every gate, the build and every walk green; the seed and the figures above ran on a scratch copy through the built files; NOTHING placed, nothing restarted"; clean; rm -rf "$WALK"; exit 0
fi
copydb "$DBF" "$FIN/finance.db.bak_S437_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ALLF[@]}"; do BAK[$f]="$FIN/$f.bak_S437_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S437_$STAMP made (backup API); .bak_S437_<from8> beside the eight files"
restore() {
  say "!! RED after placing - restoring the eight files byte-identically"
  for f in "${ALLF[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart clinic-finance || true; sleep 5
  for f in "${ALLF[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S437_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ALLF[@]}"; do \cp -p "$WALK/built/$f" "$FIN/$f" || restore; done
for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[8/10] placed; all eight md5s read back = the kit's pins"
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/stock/page/amir?count=1")
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/stock/page/loss?count=1")
say "health : finance healthz $c2 · /finance/stock/page/amir $c3 · /finance/stock/page/loss $c4 without a login (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[9/10] clinic-finance active, healthz 200, the pages behind their login gate, nothing 'NOT mounted'"
SOUT="$( cd /tmp && env FINANCE_SSO_DIR=$POR "$SPY" -B "$KDIR/seed_s437.py" --app "$FIN" --db "$DBF" 2>&1 )" || { echo "$SOUT" | tail -20; restore; }
echo "$SOUT" | sed 's/^/   /'
copydb "$DBF" "$WALK/fig/scratch_fig.db" && ( cd "$WALK/fig" && env FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR FINANCE_DB="$WALK/fig/scratch_fig.db" timeout 900 "$SPY" -B "$KDIR/figures_s437.py" --app "$FIN" --db "$WALK/fig/scratch_fig.db" 2>&1 ) | sed 's/^/   /'
say "[10/10] the seed ran on the live database (the whole-piece list, the STOCK RECEIVE round by rule); the figures (above, on a fresh scratch copy through the live files)"
clean; rm -rf "$WALK"
for f in "${ALLF[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/stock/page/amir?count=1 · https://followup.dr-manoj.in/finance/stockmatch · https://followup.dr-manoj.in/finance/stock/page/loss?count=1"
