#!/bin/bash
# =============================================================================
#  install_S431_COUNT_STATEMENT.sh · kit S431_COUNT_STATEMENT (session 283, 27-Sep-2026) · Sanjeevni
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S431_COUNT_STATEMENT/install_S431_COUNT_STATEMENT.sh
#  (DRY=1 runs every gate, the build and every walk, and places nothing. KITS=<dir> names the folder holding the S404/S427/S428/S430
#   kits when this kit is run from a copy.)
#
#  THE COUNT OF 06-09-2026 AS ONE STATEMENT, SECTION BY SECTION (the owner, 27-Sep 13:0x): Medicines · Consumables · Orthotics from his
#  map, every counted line once (matched lines collapsed, never dropped), Marg / physical / the confirmed swap / shortage and excess after
#  swaps / value at SELLING PRICE (the spine's S.RATE, else MRP, else the 0.30 rule, else rate / margin, else 'no price -- name it') / what
#  became of it (the S427 close's group; Darpan's reason and the voucher state for orthotics). The orthotic block at the top of its
#  section. 'Freeze this statement' keeps a dated, fingerprinted copy (PDF + XLSX). Hub and old report point at it.
#
#  NEW (shipped in the kit):  /root/finance/stock_statement.py (v1.0), /root/finance/stock_statement.html
#  PATCHED ON THE BOX from the live bytes (make_s431.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/stock_app.py        0e0fc043 -> see TO   the S418-way import, the statement routes, the hub's and the report's links
#          /root/finance/stock_hub.html      74ea0699 -> see TO   the first card's statement links; the status card names old stock / owner's use
#          /root/finance/stock_report.html   bd750dc8 -> see TO   'closed on <date> -- see the statement' in place of the decision-desk block
#  Restarts clinic-finance ONLY. No data change (the stock_statement table is created on first read; a freeze is the owner's tap).
#  The walk (this kit's, with its negative control), then S430's, S427's (S430 adjustments), S428's (S430 adjustment) and S404's walks
#  re-run on the patched files, each against its own pre-kit control and on the database backup its scenario needs.
# =============================================================================
set -u
KIT="S431_COUNT_STATEMENT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
K404="$(cd "$KITS/S404_ORTHO_STOCK_CLOSE" 2>/dev/null && pwd)"
K427="$(cd "$KITS/S427_LOSS_DESK_RULINGS" 2>/dev/null && pwd)"
K428="$(cd "$KITS/S428_STOCK_WATCH" 2>/dev/null && pwd)"
K430="$(cd "$KITS/S430_DESK_FIRST_READ" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"
DBF="${FINANCE_DB:-$FIN/finance.db}"; SPDB="$FIN/spine/spine.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s431_walk_$STAMP"
declare -A FROM=( [stock_app.py]=0e0fc043c4bbae75c6f1fc8149547cb7 [stock_hub.html]=74ea06997b900e9f55c47dca473a9232 [stock_report.html]=bd750dc8a32c0ed6baf66f48d7114c90 )
declare -A TO=( [stock_app.py]=2a95e2543330b3efbdb0dc0106892bea [stock_hub.html]=38e0537cd7d1eb3fb40d1a5a0b7df0e5 [stock_report.html]=610169c04c4de54724fb4e754d572eab
                [stock_statement.py]=85ec7619d79c7a9f311f7bed91eeabae [stock_statement.html]=175f4654a88e6bb81d0fd724be6d93c4 )
PATCHED=(stock_app.py stock_hub.html stock_report.html)
NEWF=(stock_statement.py stock_statement.html)
ALLF=("${PATCHED[@]}" "${NEWF[@]}")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K404" "$K427" "$K428" "$K430" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K404/walk_s404.py" "$K404/seed_s404.py" "$K427/seed_s427.py" "$K428/seed_s428.py" "$K430/walk_s430.py" "$K430/seed_s430.py" "$K430/walk_s427_s430.py" "$K430/walk_s428_s430.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS) - the earlier walks re-run; nothing installed"; exit 1; }
done
"$VPY" -c "import pywebpush, flask, pypdf, openpyxl" 2>/dev/null || { say "!! [1/10] the venv python lacks pywebpush / flask / pypdf / openpyxl (the walks need them); nothing installed"; exit 1; }
[ -f "$SPDB" ] || { say "!! [1/10] the spine $SPDB is not there (the statement prices from it); nothing installed"; exit 1; }
say "[1/10] kit gates green (SUMS, KIT_ID, the S404/S427/S428/S430 walks found, the venv modules, the spine)"
ALL=1; for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the five files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance); healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"; exit 0; fi
for f in "${PATCHED[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
for f in "${NEWF[@]}"; do [ -e "$FIN/$f" ] && { say "!! [2/10] $FIN/$f already exists ($(m5 "$FIN/$f")) - not this kit's; nothing installed"; exit 1; }; done
say "[2/10] the three live files at their FROM pins; stock_statement.py / .html not there yet"
S428_BAK="$FIN/finance.db.bak_S428_20260927_103804"     # the database as S428's install found it (10:38 IST): S427's walk runs there (the count still open, the parked lines as S427 froze them)
S430_BAK="$FIN/finance.db.bak_S430_20260927_121728"     # the database as S430's install found it (12:17 IST, before the owner closed the count at 12:58): S430's and S428's walks run there
S412_BAK="$FIN/finance.db.bak_S412_20260926_140429"     # S404's walk's database, as every kit since S404 re-ran it
for b in "$S428_BAK" "$S430_BAK" "$S412_BAK"; do [ -f "$b" ] || { say "!! [2/10] $b is not there (an earlier walk re-runs on it); nothing installed"; exit 1; }; done
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" \
         "$WALK/old430/finance_ui" "$WALK/old430/spine" "$WALK/old427/finance_ui" "$WALK/old427/spine" "$WALK/old428/finance_ui" "$WALK/old428/spine" \
         "$WALK/old404/finance_ui" "$WALK/old404/spine" "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/p403" "$WALK/p404" "$WALK/uploads" "$WALK/stub" "$WALK/fig" || exit 1
"$SPY" -B make_s431.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
cp -p "$KDIR/stock_statement.py" "$KDIR/stock_statement.html" "$WALK/built/"
for f in "${ALLF[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/10] live bytes + anchored edits give exactly the kit's files (five pins match)"
( "$SPY" -m py_compile make_s431.py walk_s431.py figures_s431.py "$WALK/built/stock_app.py" "$WALK/built/stock_statement.py" 2>/dev/null \
  && "$VPY" -m py_compile walk_s431.py figures_s431.py "$WALK/built/stock_app.py" "$WALK/built/stock_statement.py" 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in finance old old430 old427 old428 old404; do
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
  cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$FIN/spine/spine.db" "$WALK/$side/spine/" 2>/dev/null
done
for f in "${ALLF[@]}"; do cp -p "$WALK/built/$f" "$WALK/finance/$f"; done
# old430 = before S430 (S430's own negative control): its five .bak_S430 files
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
# the earlier walks import their seeds from beside themselves: the kits' seeds and walks, copied together
cp -p "$K427/seed_s427.py" "$K428/seed_s428.py" "$K430/seed_s430.py" "$K430/walk_s430.py" "$K430/walk_s427_s430.py" "$K430/walk_s428_s430.py" "$WALK/" || { say "!! [5/10] the S427/S428/S430 seeds and walks must be reachable (KITS=$KITS)"; rm -rf "$WALK"; exit 1; }
copydb "$DBF" "$WALK/scratch1.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$S430_BAK" "$WALK/scratch430.db" || { rm -rf "$WALK"; exit 1; }
copydb "$S430_BAK" "$WALK/scratch428.db" || { rm -rf "$WALK"; exit 1; }
copydb "$S428_BAK" "$WALK/scratch427.db" || { say "!! [5/10] no scratch copy of $S428_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$S412_BAK" "$WALK/scratch404.db" || { say "!! [5/10] no scratch copy of $S412_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$SPDB" "$WALK/spine_scratch.db" || { say "!! [5/10] no scratch copy of the spine - nothing installed"; rm -rf "$WALK"; exit 1; }
for i in 430 427 428; do copydb "$SPDB" "$WALK/spine_scratch$i.db" || { rm -rf "$WALK"; exit 1; }; done
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" SPINE_DB="$WALK/spine_scratch.db" timeout 2400 "$VPY" -B "$KDIR/walk_s431.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" --spine "$WALK/spine_scratch.db" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S431 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s431 green on scratch copies of the live database and the spine, its negative control red on the box as it is (above)"
W430="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch430.db" SPINE_DB="$WALK/spine_scratch430.db" timeout 2400 "$VPY" -B "$WALK/walk_s430.py" --app "$WALK/finance" --old "$WALK/old430" --db "$WALK/scratch430.db" --spine "$WALK/spine_scratch430.db" 2>&1 )"
echo "$W430" | grep -E '^(WALK_S430|  FAIL|-- )' | sed 's/^/   /'
echo "$W430" | grep -q "^WALK_S430 GREEN" || { say "!! [6/10] S430's walk went red on the patched files - nothing installed"; echo "$W430" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W427="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch427.db" SPINE_DB="$WALK/spine_scratch427.db" timeout 2400 "$VPY" -B "$WALK/walk_s427_s430.py" --app "$WALK/finance" --old "$WALK/old427" --db "$WALK/scratch427.db" --spine "$WALK/spine_scratch427.db" 2>&1 )"
echo "$W427" | grep -E '^(WALK_S427|  FAIL|-- )' | sed 's/^/   /'
echo "$W427" | grep -q "^WALK_S427 GREEN" || { say "!! [6/10] S427's walk (S430 adjustments) went red - nothing installed"; echo "$W427" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W428="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch428.db" SPINE_DB="$WALK/spine_scratch428.db" timeout 2400 "$VPY" -B "$WALK/walk_s428_s430.py" --app "$WALK/finance" --old "$WALK/old428" --db "$WALK/scratch428.db" --spine "$WALK/spine_scratch428.db" 2>&1 )"
echo "$W428" | grep -E '^(WALK_S428|  FAIL|-- )' | sed 's/^/   /'
echo "$W428" | grep -q "^WALK_S428 GREEN" || { say "!! [6/10] S428's walk (S430 adjustment) went red - nothing installed"; echo "$W428" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W404="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch404.db" SPINE_DB="$WALK/spine_scratch.db" timeout 1500 "$VPY" -B "$K404/walk_s404.py" --app "$WALK/finance" --old "$WALK/old404" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch404.db" --portal-new "$WALK/p403" --portal-old "$WALK/p404" 2>&1 )"
echo "$W404" | grep -E '^(WALK_S404|  FAIL|-- )' | sed 's/^/   /'
echo "$W404" | grep -q "^WALK_S404 GREEN" || { say "!! [6/10] S404's walk went red on the patched files - nothing installed"; echo "$W404" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S430's walk and S428's (on the 12:17 backup of 27-Sep, before the close), S427's (on the 10:38 backup) and S404's (on the 14:04 backup of 26-Sep) re-run on the patched files, each against its own pre-kit control: green (above)"
if [ "${DRY:-0}" = 1 ]; then
  copydb "$DBF" "$WALK/fig/scratch_fig.db" && ( cd "$WALK/fig" && env $WENV FINANCE_DB="$WALK/fig/scratch_fig.db" timeout 900 "$SPY" -B "$KDIR/figures_s431.py" --app "$WALK/finance" --db "$WALK/fig/scratch_fig.db" 2>&1 ) | sed 's/^/   /'
  say "-- DRY RUN: every gate, the build and every walk green; the figures above read on a scratch copy through the built files; NOTHING placed, nothing restarted"; clean; rm -rf "$WALK"; exit 0
fi
copydb "$DBF" "$FIN/finance.db.bak_S431_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${PATCHED[@]}"; do BAK[$f]="$FIN/$f.bak_S431_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S431_$STAMP made (backup API); .bak_S431_<from8> beside the three patched files"
restore() {
  say "!! RED after placing - restoring the three files byte-identically, removing the two new ones"
  for f in "${PATCHED[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  for f in "${NEWF[@]}"; do rm -f "$FIN/$f"; done
  systemctl restart clinic-finance || true; sleep 5
  for f in "${PATCHED[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S431_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ALLF[@]}"; do \cp -p "$WALK/built/$f" "$FIN/$f" || restore; done
for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[8/10] placed; all five md5s read back = the kit's pins"
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/stock/page/statement?count=1")
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/stock/page/hub?count=1")
say "health : finance healthz $c2 · /finance/stock/page/statement $c3 · /finance/stock/page/hub $c4 without a login (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[9/10] clinic-finance active, healthz 200, the statement behind its login gate, nothing 'NOT mounted'"
copydb "$DBF" "$WALK/fig/scratch_fig.db" && ( cd "$WALK/fig" && env FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR FINANCE_DB="$WALK/fig/scratch_fig.db" timeout 900 "$SPY" -B "$KDIR/figures_s431.py" --app "$FIN" --db "$WALK/fig/scratch_fig.db" 2>&1 ) | sed 's/^/   /'
say "[10/10] the statement's figures (above, read on a fresh scratch copy through the live files)"
clean; rm -rf "$WALK"
for f in "${ALLF[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/stock/page/statement?count=1"
