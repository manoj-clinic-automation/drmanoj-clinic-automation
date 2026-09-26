#!/bin/bash
# =============================================================================
#  install_S404_ORTHO_STOCK_CLOSE.sh · kit S404_ORTHO_STOCK_CLOSE (session 283, Sanjeevni, 26-Sep-2026, D619 / D620)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S404_ORTHO_STOCK_CLOSE/install_S404_ORTHO_STOCK_CLOSE.sh
#
#  THE OWNER (26-Sep-2026): close the stock check for the ORTHOTIC section first. Darpan gets an interactive tool
#  (phone or PC) for the matches -- Adla-badli? Haan / Nahi per pair, Kam kyun? one reason chip per line -- and Amir
#  changes the 22 names in Marg from a tick-list on his board; the server follows the rename and reads it back from
#  Marg's next export. The hub gains the orthotic section: Darpan's answers, the orthotic voucher round, the verdict
#  'Orthotics section: CLOSED on <date>' when all four conditions hold.
#
#  NEW:    /root/finance/stockmatch.py + stockmatch.html (unit 'stockmatch': darpan maker, manoj checker -- seeded)
#          /root/finance/item_alias.py (the rename memory: marg_item_rename, seeded with the 22)
#  PATCHED ON THE BOX from the live bytes (make_s404.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/stock_app.py            1b473fbf -> 586ae78a
#          /root/finance/stock_hub.html          c4f3280b -> 68d11419
#          /root/finance/stock_amir.html         14024b8d -> c2ea41b2
#          /root/finance/section_map.py          b05b0f08 -> 9bf9b98f
#          /root/finance/spine/spine_build.py    1378c87d -> ce99bedf   (read by the nightly spine build; not run here)
#          /root/marg_ingest/marg_take.py        75b8056c -> 21e37b0e   (the one door; fail-soft hook)
#          /root/finance/finance_app.py          d7ee72c5 -> 186a500a   (unit map + guarded mount only)
#          /root/portal/portal.py                592ccf99 -> 4a5b505e   (the tile)
#          /root/portal/tile_grants.json         9231cefa -> 9e3124e0   (v26 -> v27, the tile to darpan)
#  Restarts clinic-finance and clinic-portal only. finance.db backed up first; the seed adds 1 unit, 2 role rows,
#  22 rename rows. The walk (this kit's, then S400's and S402's re-run on the patched files) runs on scratch copies.
# =============================================================================
set -u
KIT="S404_ORTHO_STOCK_CLOSE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
K400="$(cd "$KDIR/../S400_MEDICAL_SALE_CHECK" 2>/dev/null && pwd)"
K402="$(cd "$KDIR/../S402_SALECHECK_RETURNS" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s404_walk_$STAMP"
declare -A FROM=( [stock_app.py]=1b473fbf586dea13edd40a6a993cb2ba [stock_hub.html]=c4f3280b2d005b39c02d3f6eed13c3ec
                  [stock_amir.html]=14024b8dfc64c76959ec12f43e0a4f88 [section_map.py]=b05b0f08ad65519675e21c9a6f4e90a0
                  [spine_build.py]=1378c87de2f8d4b3796cd92c7ca50d8d [marg_take.py]=75b8056cc43ad6f3034ea1fa819ed7a8
                  [finance_app.py]=d7ee72c51564a397f4e847e98eb80ddc [portal.py]=592ccf99d02c361d4d5eb580995599c3
                  [tile_grants.json]=9231cefad0897a64aa127ce4a448f4fe )
declare -A TO=( [stock_app.py]=586ae78ae6437f806692c2a1e4eeeb37 [stock_hub.html]=68d11419e7fb9a8e5fec74095b60b255
                [stock_amir.html]=c2ea41b2db7e2b337e0a97426aaed763 [section_map.py]=9bf9b98fbfe64276b46c0a56ee9719e0
                [spine_build.py]=ce99bedf60194a84fe93455927a336e2 [marg_take.py]=21e37b0e6fa6505a8825b32b7c24d41d
                [finance_app.py]=186a500a862a7f77da45e1e39b504f2e [portal.py]=4a5b505e0274e37ab576fa0bc7852420
                [tile_grants.json]=9e3124e02fd79d3e1ef01e52bdc5cc76 )
declare -A DEST=( [stock_app.py]="$FIN/stock_app.py" [stock_hub.html]="$FIN/stock_hub.html" [stock_amir.html]="$FIN/stock_amir.html"
                  [section_map.py]="$FIN/section_map.py" [spine_build.py]="$FIN/spine/spine_build.py" [marg_take.py]="$MRG/marg_take.py"
                  [finance_app.py]="$FIN/finance_app.py" [portal.py]="$POR/portal.py" [tile_grants.json]="$POR/tile_grants.json" )
ORDER=(stock_app.py stock_hub.html stock_amir.html section_map.py spine_build.py marg_take.py finance_app.py portal.py tile_grants.json)
NEWF=(item_alias.py stockmatch.py stockmatch.html)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K400" "$K402" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$K400" ] && [ -f "$K400/walk_s400.py" ] && [ -f "$K400/seed_s400.py" ] || { say "!! [1/10] the S400 kit (its walk) must sit beside this kit - nothing installed"; exit 1; }
[ -n "$K402" ] && [ -f "$K402/walk_s402.py" ] || { say "!! [1/10] the S402 kit (its walk) must sit beside this kit - nothing installed"; exit 1; }
say "[1/10] kit gates green (S400's and S402's walks found)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED. Seed re-checked:"; "$SPY" -B seed_s404.py "$DBF" --finance "$FIN"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/10] ${DEST[$f]} is $(m5 "${DEST[$f]}"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] every live file at its FROM pin"
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" "$WALK/old0/finance_ui" "$WALK/old2/finance_ui" \
         "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/pnew" "$WALK/pold" "$WALK/plive" "$WALK/uploads" "$WALK/stub" || exit 1
"$SPY" -B make_s404.py --finance "$FIN" --portal "$POR" --marg "$MRG" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/10] live bytes + anchored edits give exactly the kit's nine files (pins match)"
( "$SPY" -m py_compile item_alias.py stockmatch.py seed_s404.py make_s404.py walk_s404.py "$WALK/built/stock_app.py" "$WALK/built/section_map.py" "$WALK/built/spine_build.py" "$WALK/built/marg_take.py" "$WALK/built/finance_app.py" "$WALK/built/portal.py" \
  && "$VPY" -m py_compile item_alias.py stockmatch.py seed_s404.py "$WALK/built/stock_app.py" "$WALK/built/section_map.py" "$WALK/built/spine_build.py" "$WALK/built/marg_take.py" "$WALK/built/finance_app.py" "$WALK/built/portal.py" 2>/dev/null \
  && "$VPY" -c "import json,sys; assert json.load(open(sys.argv[1],encoding='utf-8'))['version']==27" "$WALK/built/tile_grants.json" ) \
  || { say "!! [4/10] compile on both pythons / json failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python; grants v27"
# the walk's copies of the box: finance (new), old (as it is), old0 (pre-S400), old2 (pre-S402); marg_ingest (new) and marg_old
for side in finance old old0 old2; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
done
cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/finance/spine/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/old/spine/" 2>/dev/null
cp -p "$WALK/built/stock_app.py" "$WALK/built/stock_hub.html" "$WALK/built/stock_amir.html" "$WALK/built/section_map.py" "$WALK/built/finance_app.py" "$WALK/finance/"
cp -p "$WALK/built/spine_build.py" "$WALK/finance/spine/"
cp -p item_alias.py stockmatch.py stockmatch.html "$WALK/finance/"
for side in marg_ingest marg_old; do cp -p "$MRG"/*.py "$WALK/$side/" 2>/dev/null; cp -rp "$MRG/xlrd" "$WALK/$side/xlrd" 2>/dev/null; [ -d "$MRG/lib" ] && cp -rp "$MRG/lib" "$WALK/$side/lib"; done
cp -p "$WALK/built/marg_take.py" "$WALK/marg_ingest/"
# old0 = the box BEFORE S400 (its .bak_S400 files), the negative control S400's own walk expects; old2 = before S402
for pair in "finance_app.py:70cff498" "sanjeevni_day.py:5d16eff5" "sanjeevni_approvals.py:7ab5fec6"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S400_$h" "$WALK/old0/$f" || { say "!! [5/10] $f.bak_S400_$h missing - cannot rebuild the pre-S400 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S400_750f89e0" "$WALK/old0/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old0/sale_check.py" "$WALK/old0/sale_check.html"
cp -p "$FIN/sale_check.py.bak_S402_81cccad3" "$WALK/old2/sale_check.py" && cp -p "$FIN/sale_check.html.bak_S402_4202d11b" "$WALK/old2/sale_check.html" || { say "!! [5/10] the .bak_S402 files are missing - cannot rebuild the pre-S402 control"; rm -rf "$WALK"; exit 1; }
cp -p "$POR"/*.py "$WALK/pnew/"; cp -p "$WALK/built/portal.py" "$WALK/built/tile_grants.json" "$WALK/pnew/"
cp -p "$POR"/*.py "$WALK/plive/"; cp -p "$POR/tile_grants.json" "$WALK/plive/"
cp -p "$POR"/*.py "$WALK/pold/"; cp -p "$POR/portal.py.bak_S400_80d6dc44" "$WALK/pold/portal.py"; cp -p "$POR/tile_grants.json.bak_S400_7d195476" "$WALK/pold/tile_grants.json"
copydb "$DBF" "$WALK/scratch1.db" && copydb "$DBF" "$WALK/scratch2.db" && copydb "$DBF" "$WALK/scratch3.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 1500 "$VPY" -B "$KDIR/walk_s404.py" --app "$WALK/finance" --old "$WALK/old" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch1.db" --portal-new "$WALK/pnew" --portal-old "$WALK/plive" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S404 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s404 green on a scratch copy of the live database (above)"
W400="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch2.db" timeout 900 "$VPY" -B "$K400/walk_s400.py" --app "$WALK/finance" --old "$WALK/old0" --db "$WALK/scratch2.db" --portal-new "$WALK/plive" --portal-old "$WALK/pold" 2>&1 )"
echo "$W400" | grep -E '^(WALK_S400|  FAIL|-- )' | sed 's/^/   /'
echo "$W400" | grep -q "^WALK_S400 GREEN" || { say "!! [6/10] S400's walk went red on the patched files - nothing installed"; echo "$W400" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W402="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch3.db" timeout 900 "$VPY" -B "$K402/walk_s402.py" --app "$WALK/finance" --old "$WALK/old2" --db "$WALK/scratch3.db" 2>&1 )"
echo "$W402" | grep -E '^(WALK_S402|  FAIL|-- )' | sed 's/^/   /'
echo "$W402" | grep -q "^WALK_S402 GREEN" || { say "!! [6/10] S402's walk went red on the patched files - nothing installed"; echo "$W402" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S400's and S402's own walks re-run on the patched files: still green (above)"
copydb "$DBF" "$FIN/finance.db.bak_S404_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S404_$(m5 "${DEST[$f]}" | cut -c1-8)"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S404_$STAMP made; .bak_S404_<from8> beside each of the nine files"
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  for f in "${NEWF[@]}"; do rm -f "$FIN/$f"; done
  systemctl restart clinic-finance clinic-portal || true; sleep 4
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S404_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "${DEST[$f]}" || restore; done
for f in "${NEWF[@]}"; do \cp -p "$f" "$FIN/$f" && chmod 644 "$FIN/$f" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || restore; done
find "$FIN" "$FIN/spine" "$MRG" -maxdepth 1 -name __pycache__ -prune -exec sh -c 'rm -f "$1"/stock_app*.pyc "$1"/section_map*.pyc "$1"/spine_build*.pyc "$1"/marg_take*.pyc "$1"/finance_app*.pyc' _ {} \; 2>/dev/null
say "[8/10] placed; every md5 read back = the kit's pin"
"$SPY" -B seed_s404.py "$DBF" --finance "$FIN" || restore
say "[9/10] stockmatch unit seeded (darpan maker, manoj checker); rename memory seeded (22)"
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 5
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || restore; done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stockmatch)
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/stock/page/hub?count=1")
say "health : finance healthz $c2 · portal $c3 · /finance/stockmatch without a login $c4 · the hub without a login $c5 (302 = the login gate, expected)"
[ "$c2" = 200 ] && { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } && { [ "$c5" = 302 ] || [ "$c5" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[10/10] clinic-finance + clinic-portal active, healthz 200, nothing 'NOT mounted'"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
for f in "${NEWF[@]}"; do md5sum "$FIN/$f"; done
"$SPY" -B "$FIN/item_alias.py" --status "$DBF" | tail -1
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/stockmatch (tile 'Stock milaan' for darpan and the owner); the hub: https://followup.dr-manoj.in/finance/stock/page/hub?count=1"
