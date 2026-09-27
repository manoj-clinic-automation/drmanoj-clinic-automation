#!/bin/bash
# =============================================================================
#  install_S427_LOSS_DESK_RULINGS.sh · kit S427_LOSS_DESK_RULINGS (session 283, 27-Sep-2026, D632, F-642) · Sanjeevni
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S427_LOSS_DESK_RULINGS/install_S427_LOSS_DESK_RULINGS.sh
#  (DRY=1 runs every gate, the build and every walk, and places nothing. KITS=<dir> names the folder holding the
#   S403/S404 kits when this kit is run from a copy.)
#
#  THE OWNER'S LOSS DESK UNDER HIS RULINGS OF 27-Sep (runs after S418):
#   * ONE nomenclature -- qty_words.py: strips + tabs / pcs / bottles / tubes / vials (Hindi patte / goli / nag); the
#     word 'unit(s)' reaches no screen, hint, PDF or message; stock_app._qw routes through it
#   * FOUR PILES by turnover: With me / Write off (within the allowance = % of the item's OWN sales since the previous
#     count; small real gap) / Big losses (by value, or a slow item, or never sold) / Consumption (the owner's list only)
#   * NO recount pile: Darpan's own 'Dobara ginna hai' on Stock milaan (any item); /pile/recount answers 410
#   * the sales-after-count test closes a line the system can prove existed (sold since > counted + bought since)
#   * ONE tap closes the count: piles 2-4 written off, Amir's vouchers, one frozen run with four groups, THE STAFF BLOCK
#     (Hindi, pinned on Stock milaan) -- total loss / small part written off / big losses BY NAME
#   * every threshold a setting on the desk (audited); the S418 dial and recount keys leave the card
#
#  PATCHED ON THE BOX from the live bytes (make_s427.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/stock_app.py        cf464882 -> see TO   qty_words, the sales test, 410, close, items, five texts
#          /root/finance/stock_hub.html      bb8741fa -> see TO   the status card's new piles, step 3, the swap texts
#          /root/finance/stockmatch.py       d5f9392f -> see TO   the block, Dobara ginna hai, items, note
#          /root/finance/stockmatch.html     9a090e03 -> see TO   the cards
#          /root/finance/stock_amir.html     c2ea41b2 -> see TO   the JS helper's name only (quantity words unchanged)
#  REPLACED (whole file, shipped in the kit):   /root/finance/loss_piles.py   3b6554f8 -> see TO   v2.0
#                                               /root/finance/stock_loss.html 16cdddaa -> see TO
#  NEW:                                         /root/finance/qty_words.py
#  DATA: seed_s427.py on the live database after the backup and a green restart -- the desk's settings, written only
#  where absent (the big-loss floor inherits the S418 pursue floor's value; the consumption list seeded). Restarts
#  clinic-finance ONLY. The walk (this kit's, with its negative control on the box as it is), then S404's walk (on the
#  14:04 backup of 26-Sep, as S414/S417/S418 ran it) and S403's walk (on the 17:45 backup) re-run on the patched files.
# =============================================================================
set -u
KIT="S427_LOSS_DESK_RULINGS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
K403="$(cd "$KITS/S403_PURCHASE_ORDERS_LIVE" 2>/dev/null && pwd)"
K404="$(cd "$KITS/S404_ORTHO_STOCK_CLOSE" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPDB="$FIN/spine/spine.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s427_walk_$STAMP"
S412_BAK="$FIN/finance.db.bak_S412_20260926_140429"
S414_BAK="$FIN/finance.db.bak_S414_20260926_174505"
declare -A FROM=( [stock_app.py]=cf464882e49865f38153e1df6218301d [stock_hub.html]=bb8741fa7671399f9c495c75946d7c11
                  [stockmatch.py]=d5f9392fea4247b37705e865e1c242cb [stockmatch.html]=9a090e03c954bfda5a787e8d834f275c
                  [stock_amir.html]=c2ea41b2db7e2b337e0a97426aaed763 [loss_piles.py]=3b6554f86507509e0b1893129e748274
                  [stock_loss.html]=16cdddaa6363ccc8da0278fa5d4635a3 )
declare -A TO=( [stock_app.py]=24c2b5fe7cacfe238751e487e52eb6d0 [stock_hub.html]=74ea06997b900e9f55c47dca473a9232
                [stockmatch.py]=e85807dab1f8672d482272e0d355fe28 [stockmatch.html]=ecd039f4f64d5be6a15d7ffbbcdf3950
                [stock_amir.html]=244ac6eeb0117b14f2c3c7fa1576f728 [loss_piles.py]=9dc06c9000539b6fbf3f77ddac967c7d
                [stock_loss.html]=fdd913e75677580a7897fe2631196c4c [qty_words.py]=1e67a3e35ce815798ef6ebd606e5b972 )
PATCHED=(stock_app.py stock_hub.html stockmatch.py stockmatch.html stock_amir.html)
ORDER=("${PATCHED[@]}" loss_piles.py stock_loss.html)
ALLF=("${ORDER[@]}" qty_words.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K403" "$K404" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K403/walk_s403.py" "$K403/seed_s403.py" "$K404/walk_s404.py" "$K404/seed_s404.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS) - the earlier walks re-run; nothing installed"; exit 1; }
done
"$VPY" -c "import pywebpush, flask, pypdf, openpyxl" 2>/dev/null || { say "!! [1/10] the venv python lacks pywebpush / flask / pypdf / openpyxl (the walks need them); nothing installed"; exit 1; }
[ -f "$SPDB" ] || { say "!! [1/10] the spine $SPDB is not there - the allowance and the sales test read it; nothing installed"; exit 1; }
say "[1/10] kit gates green (SUMS, KIT_ID, the S403/S404 walks found, the venv modules, the spine)"
ALL=1; for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the eight files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance); healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
[ -e "$FIN/qty_words.py" ] && { say "!! [2/10] $FIN/qty_words.py already exists ($(m5 "$FIN/qty_words.py")) - not this kit's; nothing installed"; exit 1; }
say "[2/10] the seven live files at their FROM pins; qty_words.py not there yet"
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" \
         "$WALK/old404/finance_ui" "$WALK/old404/spine" "$WALK/old403/finance_ui" "$WALK/old403/spine" \
         "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/assetapp_live" "$WALK/assetapp_old3" "$WALK/p408" "$WALK/p403" "$WALK/p404" \
         "$WALK/uploads" "$WALK/stub" "$WALK/fig" || exit 1
"$SPY" -B make_s427.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
cp -p "$KDIR/loss_piles.py" "$KDIR/stock_loss.html" "$KDIR/qty_words.py" "$WALK/built/"
for f in "${ALLF[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/10] live bytes + anchored edits give exactly the kit's files (eight pins match)"
( "$SPY" -m py_compile make_s427.py walk_s427.py seed_s427.py figures_s427.py "$WALK/built/stock_app.py" "$WALK/built/stockmatch.py" "$WALK/built/loss_piles.py" "$WALK/built/qty_words.py" 2>/dev/null \
  && "$VPY" -m py_compile walk_s427.py seed_s427.py figures_s427.py "$WALK/built/stock_app.py" "$WALK/built/stockmatch.py" "$WALK/built/loss_piles.py" "$WALK/built/qty_words.py" 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in finance old old404 old403; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
  cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null
done
for side in finance old old403; do cp -p "$SPDB" "$WALK/$side/spine/"; done
for f in "${ALLF[@]}"; do cp -p "$WALK/built/$f" "$WALK/finance/$f"; done
# old404 = before S404 (S404's own negative control)
for pair in "stock_app.py:1b473fbf" "stock_hub.html:c4f3280b" "stock_amir.html:14024b8d" "section_map.py:b05b0f08" "finance_app.py:d7ee72c5"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S404_$h" "$WALK/old404/$f" || { say "!! [5/10] $f.bak_S404_$h missing - cannot rebuild the pre-S404 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/spine/spine_build.py.bak_S404_1378c87d" "$WALK/old404/spine/spine_build.py" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old404/item_alias.py" "$WALK/old404/stockmatch.py" "$WALK/old404/stockmatch.html" "$WALK/old404/loss_piles.py" "$WALK/old404/qty_words.py"
for side in marg_ingest marg_old; do cp -p "$MRG"/*.py "$WALK/$side/" 2>/dev/null; cp -rp "$MRG/xlrd" "$WALK/$side/xlrd" 2>/dev/null; [ -d "$MRG/lib" ] && cp -rp "$MRG/lib" "$WALK/$side/lib"; done
cp -p "$MRG/marg_take.py.bak_S404_75b8056c" "$WALK/marg_old/marg_take.py" || { say "!! [5/10] marg_take.py.bak_S404_75b8056c missing"; rm -rf "$WALK"; exit 1; }
# old403 = before S403 (S403's own negative control)
for pair in "purchase_app.py:9ad50878" "darpan_kal.py:1958ee7c" "darpan_kal.html:4f115f44" "sale_check.py:92ca5cb2" "sale_check.html:9c70af26" "sanjeevni_approvals.py:5fdfa364" "finance_app.py:186a500a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S403_$h" "$WALK/old403/$f" || { say "!! [5/10] $f.bak_S403_$h missing - cannot rebuild the pre-S403 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S403_6622587e" "$WALK/old403/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old403/porders.py" "$WALK/old403/porders.html"
for side in assetapp_live assetapp_old3; do cp -p "$AST"/*.py "$AST"/*.js "$WALK/$side/" 2>/dev/null; done
cp -p "$AST/asset_register.py.bak_S403_71bd3277" "$WALK/assetapp_old3/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S403_71bd3277 missing"; rm -rf "$WALK"; exit 1; }
# the portals: before S408 (v28) · before S403 (v27) · before S404
cp -p "$POR"/*.py "$WALK/p408/"; cp -p "$POR/portal.py.bak_S408_968ca602" "$WALK/p408/portal.py"; cp -p "$POR/tile_grants.json.bak_S408_0aadfc52" "$WALK/p408/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p404/"; cp -p "$POR/portal.py.bak_S404_592ccf99" "$WALK/p404/portal.py"; cp -p "$POR/tile_grants.json.bak_S404_9231cefa" "$WALK/p404/tile_grants.json"
copydb "$DBF" "$WALK/scratch1.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$SPDB" "$WALK/spine_scratch.db" || { say "!! [5/10] no scratch copy of the spine - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$ADB" "$WALK/assets_scratch1.db" || { say "!! [5/10] no scratch copy of assets.db - nothing installed"; rm -rf "$WALK"; exit 1; }
# S404's frozen walk answers two OPEN swap pairs of the real count 1: its scratch is the 14:04 backup of 26-Sep (declared by S414, kept by S417/S418)
copydb "$S412_BAK" "$WALK/scratch404.db" || { say "!! [5/10] no scratch copy of $S412_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
# S403's frozen walk asserts the buying rules not yet approved: its scratch is the 17:45 backup of 26-Sep (declared by S417)
copydb "$S414_BAK" "$WALK/scratch403.db" || { say "!! [5/10] no scratch copy of $S414_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" SPINE_DB="$WALK/spine_scratch.db" timeout 2400 "$VPY" -B "$KDIR/walk_s427.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" --spine "$WALK/spine_scratch.db" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S427 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s427 green on scratch copies of the live database and the spine, its negative control red on the box as it is (above)"
W404="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch404.db" SPINE_DB="$WALK/spine_scratch.db" timeout 1500 "$VPY" -B "$K404/walk_s404.py" --app "$WALK/finance" --old "$WALK/old404" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch404.db" --portal-new "$WALK/p403" --portal-old "$WALK/p404" 2>&1 )"
echo "$W404" | grep -E '^(WALK_S404|  FAIL|-- )' | sed 's/^/   /'
echo "$W404" | grep -q "^WALK_S404 GREEN" || { say "!! [6/10] S404's walk went red on the patched files - nothing installed"; echo "$W404" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W403="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch403.db" SPINE_DB="$WALK/spine_scratch.db" timeout 1500 "$VPY" -B "$K403/walk_s403.py" --app "$WALK/finance" --old "$WALK/old403" \
         --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old3" --db "$WALK/scratch403.db" --assets-db "$WALK/assets_scratch1.db" \
         --portal-new "$WALK/p408" --portal-old "$WALK/p403" 2>&1 )"
echo "$W403" | grep -E '^(WALK_S403|  FAIL|-- )' | sed 's/^/   /'
echo "$W403" | grep -q "^WALK_S403 GREEN" || { say "!! [6/10] S403's walk went red on the patched files - nothing installed"; echo "$W403" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S404's (on the 14:04 backup) and S403's (on the 17:45 backup) own walks re-run on the patched files: green (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the build and every walk green; NOTHING placed, nothing restarted"; rm -rf "$WALK"; exit 0; fi
copydb "$DBF" "$FIN/finance.db.bak_S427_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="$FIN/$f.bak_S427_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S427_$STAMP made (backup API); .bak_S427_<from8> beside the seven files (qty_words.py is new)"
restore() {
  say "!! RED after placing - restoring the seven files byte-identically and removing qty_words.py"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  rm -f "$FIN/qty_words.py"
  systemctl restart clinic-finance || true; sleep 5
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   qty_words.py present: $([ -e "$FIN/qty_words.py" ] && echo yes || echo no)"
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S427_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ALLF[@]}"; do \cp -p "$WALK/built/$f" "$FIN/$f" || restore; done
for f in "${ALLF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[8/10] placed; all eight md5s read back = the kit's pins"
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/stock/page/loss?count=1")
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stockmatch)
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/stock/page/hub?count=1")
say "health : finance healthz $c2 · /finance/stock/page/loss $c3 · /finance/stockmatch $c4 · /finance/stock/page/hub $c5 without a login (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[9/10] clinic-finance active, healthz 200, the desk behind its login gate, nothing 'NOT mounted'"
SOUT="$( cd /tmp && "$SPY" -B "$KDIR/seed_s427.py" --app "$FIN" --db "$DBF" 2>&1 )" || { echo "$SOUT" | tail -20; restore; }
echo "$SOUT" | sed 's/^/   /'
copydb "$DBF" "$WALK/fig/scratch_fig.db" && ( cd "$WALK/fig" && env FINANCE_SSO_DIR=$POR timeout 900 "$SPY" -B "$KDIR/figures_s427.py" --app "$WALK/finance" --db "$WALK/fig/scratch_fig.db" 2>&1 ) | sed 's/^/   /'
say "[10/10] the desk's settings seeded on the live database (only where absent); the desk under the new rules as the owner will first see it (above, read on a fresh scratch copy)"
clean; rm -rf "$WALK"
for f in "${ALLF[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/stock/page/loss?count=1"
