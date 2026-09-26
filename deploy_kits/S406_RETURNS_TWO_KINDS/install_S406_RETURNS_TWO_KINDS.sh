#!/bin/bash
# =============================================================================
#  install_S406_RETURNS_TWO_KINDS.sh · kit S406_RETURNS_TWO_KINDS (session 283, Sanjeevni, 26-Sep-2026, D622)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S406_RETURNS_TWO_KINDS/install_S406_RETURNS_TWO_KINDS.sh
#
#  THE OWNER (26-Sep-2026): "Check the Returns section of the approvals page. Remove the lines where the difference is a
#  minor discount. Flag my own non-cash returns separately. Show what percentage of counter sales is returned at the counter."
#
#  NEW:    /root/finance/returns_kinds.py (the read layer: kind, status word, rounding, the real Need-your-OK count, the %)
#  PATCHED ON THE BOX from the live bytes (make_s406.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/darpan_app.py                      2c22822d -> 5bfabbec   cn-detail gains the fields; POST /api/cn-kind
#          /root/finance/sanjeevni_approvals.py             126f90fc -> 74fe5437   the Needs-you count; the months API fields
#          /root/finance/finance_ui/finance_approvals.html  928a25ef -> 77c79211   the Returns card re-rendered; the Month column (clinic -- declared)
#  Restarts clinic-finance only. finance.db backed up first; the seed adds three settings. No money, day, cash or Marg figure changes.
#  The walk (this kit's), then S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files -- all on scratch copies.
# =============================================================================
set -u
KIT="S406_RETURNS_TWO_KINDS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
K400="$(cd "$KDIR/../S400_MEDICAL_SALE_CHECK" 2>/dev/null && pwd)"
K402="$(cd "$KDIR/../S402_SALECHECK_RETURNS" 2>/dev/null && pwd)"
K403="$(cd "$KDIR/../S403_PURCHASE_ORDERS_LIVE" 2>/dev/null && pwd)"
K404="$(cd "$KDIR/../S404_ORTHO_STOCK_CLOSE" 2>/dev/null && pwd)"
K405="$(cd "$KDIR/../S405_BANK_SMS_DOOR" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s406_walk_$STAMP"
declare -A FROM=( [darpan_app.py]=2c22822d49a20143058b5d781eb3c06e [sanjeevni_approvals.py]=126f90fc9912092378e817f101a8f74e
                  [finance_approvals.html]=928a25ef503267ce8e518f126306c236 )
declare -A TO=( [darpan_app.py]=5bfabbecf1e0fbf86ff142e3cd07543e [sanjeevni_approvals.py]=74fe5437afd646851d0c28200592177d
                [finance_approvals.html]=77c79211845f3416a3211d22ced3d7db )
declare -A DEST=( [darpan_app.py]="$FIN/darpan_app.py" [sanjeevni_approvals.py]="$FIN/sanjeevni_approvals.py" [finance_approvals.html]="$FIN/finance_ui/finance_approvals.html" )
ORDER=(darpan_app.py sanjeevni_approvals.py finance_approvals.html)
NEWF=(returns_kinds.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K400" "$K402" "$K403" "$K404" "$K405" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K400/walk_s400.py" "$K400/seed_s400.py" "$K402/walk_s402.py" "$K403/walk_s403.py" "$K403/seed_s403.py" "$K404/walk_s404.py" "$K404/seed_s404.py" "$K405/walk_s405.py" "$K405/seed_s405.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must sit beside this kit (the S400 / S402 / S403 / S404 / S405 walks re-run) - nothing installed"; exit 1; }
done
say "[1/10] kit gates green (S400, S402, S403, S404 and S405 walks found)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED. Seed re-checked:"; "$SPY" -B seed_s406.py "$DBF"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/10] ${DEST[$f]} is $(m5 "${DEST[$f]}"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] every live file at its FROM pin"
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" "$WALK/old405/finance_ui" "$WALK/old405/spine" \
         "$WALK/old404/finance_ui" "$WALK/old404/spine" "$WALK/old403/finance_ui" "$WALK/old403/spine" "$WALK/old0/finance_ui" "$WALK/old2/finance_ui" \
         "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/assetapp_live" "$WALK/assetapp_old3" "$WALK/plive" "$WALK/p403" "$WALK/p404" "$WALK/pold" "$WALK/uploads" "$WALK/stub" || exit 1
"$SPY" -B make_s406.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/10] live bytes + anchored edits give exactly the kit's three files (pins match)"
PYS="$WALK/built/darpan_app.py $WALK/built/sanjeevni_approvals.py"
( "$SPY" -m py_compile returns_kinds.py seed_s406.py make_s406.py walk_s406.py $PYS && "$VPY" -m py_compile returns_kinds.py seed_s406.py $PYS 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
# the walk's copies of the box: finance (new) · old (as it is) · old405 · old404 · old403 · old0 · old2 (each the box before that kit)
for side in finance old old405 old404 old403 old0 old2; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
done
for side in finance old old405 old404 old403; do cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; done
[ -f "$FIN/spine/spine.db" ] && for side in finance old old405 old403; do cp -p "$FIN/spine/spine.db" "$WALK/$side/spine/"; done
cp -p "$WALK/built/darpan_app.py" "$WALK/built/sanjeevni_approvals.py" "$WALK/finance/"
cp -p "$WALK/built/finance_approvals.html" "$WALK/finance/finance_ui/"
cp -p returns_kinds.py "$WALK/finance/"
# old405 = the box BEFORE S405 (its .bak_S405 files), the negative control S405's own walk expects
for pair in "bank_sms.py:3a8f0a88" "sanjeevni_approvals.py:675aab4a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S405_$h" "$WALK/old405/$f" || { say "!! [5/10] $f.bak_S405_$h missing - cannot rebuild the pre-S405 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S405_c319bb56" "$WALK/old405/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
# old404 = the box BEFORE S404
for pair in "stock_app.py:1b473fbf" "stock_hub.html:c4f3280b" "stock_amir.html:14024b8d" "section_map.py:b05b0f08" "finance_app.py:d7ee72c5"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S404_$h" "$WALK/old404/$f" || { say "!! [5/10] $f.bak_S404_$h missing - cannot rebuild the pre-S404 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/spine/spine_build.py.bak_S404_1378c87d" "$WALK/old404/spine/spine_build.py" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old404/item_alias.py" "$WALK/old404/stockmatch.py" "$WALK/old404/stockmatch.html"
for side in marg_ingest marg_old; do cp -p "$MRG"/*.py "$WALK/$side/" 2>/dev/null; cp -rp "$MRG/xlrd" "$WALK/$side/xlrd" 2>/dev/null; [ -d "$MRG/lib" ] && cp -rp "$MRG/lib" "$WALK/$side/lib"; done
cp -p "$MRG/marg_take.py.bak_S404_75b8056c" "$WALK/marg_old/marg_take.py" || { say "!! [5/10] marg_take.py.bak_S404_75b8056c missing"; rm -rf "$WALK"; exit 1; }
# old403 = the box BEFORE S403
for pair in "purchase_app.py:9ad50878" "darpan_kal.py:1958ee7c" "darpan_kal.html:4f115f44" "sale_check.py:92ca5cb2" "sale_check.html:9c70af26" "sanjeevni_approvals.py:5fdfa364" "finance_app.py:186a500a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S403_$h" "$WALK/old403/$f" || { say "!! [5/10] $f.bak_S403_$h missing - cannot rebuild the pre-S403 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S403_6622587e" "$WALK/old403/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old403/porders.py" "$WALK/old403/porders.html"
cp -p "$AST"/*.py "$AST"/*.js "$WALK/assetapp_live/" 2>/dev/null; cp -p "$AST"/*.py "$AST"/*.js "$WALK/assetapp_old3/" 2>/dev/null
cp -p "$AST/asset_register.py.bak_S403_71bd3277" "$WALK/assetapp_old3/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S403_71bd3277 missing"; rm -rf "$WALK"; exit 1; }
# old0 = before S400; old2 = before S402
for pair in "finance_app.py:70cff498" "sanjeevni_day.py:5d16eff5" "sanjeevni_approvals.py:7ab5fec6"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S400_$h" "$WALK/old0/$f" || { say "!! [5/10] $f.bak_S400_$h missing - cannot rebuild the pre-S400 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S400_750f89e0" "$WALK/old0/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old0/sale_check.py" "$WALK/old0/sale_check.html"
cp -p "$FIN/sale_check.py.bak_S402_81cccad3" "$WALK/old2/sale_check.py" && cp -p "$FIN/sale_check.html.bak_S402_4202d11b" "$WALK/old2/sale_check.html" || { say "!! [5/10] the .bak_S402 files are missing"; rm -rf "$WALK"; exit 1; }
# the portals: live (S403, v28) · before S403 = as S404 left it (v27) · before S404 · before S400
cp -p "$POR"/*.py "$WALK/plive/"; cp -p "$POR/tile_grants.json" "$WALK/plive/"
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p404/"; cp -p "$POR/portal.py.bak_S404_592ccf99" "$WALK/p404/portal.py"; cp -p "$POR/tile_grants.json.bak_S404_9231cefa" "$WALK/p404/tile_grants.json"
cp -p "$POR"/*.py "$WALK/pold/"; cp -p "$POR/portal.py.bak_S400_80d6dc44" "$WALK/pold/portal.py"; cp -p "$POR/tile_grants.json.bak_S400_7d195476" "$WALK/pold/tile_grants.json"
for i in 1 2 3 4 5 6; do copydb "$DBF" "$WALK/scratch$i.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }; done
copydb "$ADB" "$WALK/assets_scratch.db" || { say "!! [5/10] no scratch copy of assets.db - nothing installed"; rm -rf "$WALK"; exit 1; }
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 900 "$VPY" -B "$KDIR/walk_s406.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S406 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s406 green on a scratch copy of the live database (above)"
W405="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch2.db" timeout 900 "$VPY" -B "$K405/walk_s405.py" --app "$WALK/finance" --old "$WALK/old405" --db "$WALK/scratch2.db" 2>&1 )"
echo "$W405" | grep -E '^(WALK_S405|  FAIL|-- )' | sed 's/^/   /'
echo "$W405" | grep -q "^WALK_S405 GREEN" || { say "!! [6/10] S405's walk went red on the patched files - nothing installed"; echo "$W405" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W404="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch3.db" timeout 1500 "$VPY" -B "$K404/walk_s404.py" --app "$WALK/finance" --old "$WALK/old404" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch3.db" --portal-new "$WALK/p403" --portal-old "$WALK/p404" 2>&1 )"
echo "$W404" | grep -E '^(WALK_S404|  FAIL|-- )' | sed 's/^/   /'
echo "$W404" | grep -q "^WALK_S404 GREEN" || { say "!! [6/10] S404's walk went red on the patched files - nothing installed"; echo "$W404" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W403="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch4.db" timeout 1500 "$VPY" -B "$K403/walk_s403.py" --app "$WALK/finance" --old "$WALK/old403" \
         --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old3" --db "$WALK/scratch4.db" --assets-db "$WALK/assets_scratch.db" \
         --portal-new "$WALK/plive" --portal-old "$WALK/p403" 2>&1 )"
echo "$W403" | grep -E '^(WALK_S403|  FAIL|-- )' | sed 's/^/   /'
echo "$W403" | grep -q "^WALK_S403 GREEN" || { say "!! [6/10] S403's walk went red on the patched files - nothing installed"; echo "$W403" | tail -20; clean; rm -rf "$WALK"; exit 1; }
# S400's frozen walk asserts Needs you 'unchanged except its own line'; S403's three lines and S406's real count break that by the
# owner's briefs, so that re-run alone gets NEEDS_YOU_WITHOUT_S403=1 NEEDS_YOU_WITHOUT_S406=1 (env switches the service never sets).
W400="$( cd "$WALK" && env $WENV NEEDS_YOU_WITHOUT_S403=1 NEEDS_YOU_WITHOUT_S406=1 FINANCE_DB="$WALK/scratch5.db" timeout 900 "$VPY" -B "$K400/walk_s400.py" --app "$WALK/finance" --old "$WALK/old0" --db "$WALK/scratch5.db" --portal-new "$WALK/p404" --portal-old "$WALK/pold" 2>&1 )"
echo "$W400" | grep -E '^(WALK_S400|  FAIL|-- )' | sed 's/^/   /'
echo "$W400" | grep -q "^WALK_S400 GREEN" || { say "!! [6/10] S400's walk went red on the patched files - nothing installed"; echo "$W400" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W402="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch6.db" timeout 900 "$VPY" -B "$K402/walk_s402.py" --app "$WALK/finance" --old "$WALK/old2" --db "$WALK/scratch6.db" 2>&1 )"
echo "$W402" | grep -E '^(WALK_S402|  FAIL|-- )' | sed 's/^/   /'
echo "$W402" | grep -q "^WALK_S402 GREEN" || { say "!! [6/10] S402's walk went red on the patched files - nothing installed"; echo "$W402" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files: still green (above)"
copydb "$DBF" "$FIN/finance.db.bak_S406_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S406_$(m5 "${DEST[$f]}" | cut -c1-8)"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S406_$STAMP made; .bak_S406_<from8> beside each of the three files"
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  for f in "${NEWF[@]}"; do rm -f "$FIN/$f"; done
  systemctl restart clinic-finance || true; sleep 4
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S406_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "${DEST[$f]}" || restore; done
for f in "${NEWF[@]}"; do \cp -p "$f" "$FIN/$f" && chmod 644 "$FIN/$f" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || restore; done
say "[8/10] placed; every md5 read back = the kit's pin"
"$SPY" -B seed_s406.py "$DBF" || restore
say "[9/10] the three settings seeded (returns.noise_p, returns.noise_pct, returns.big_p)"
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/approvals)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8106/finance/darpan/api/cn-detail?month=2026-09")
say "health : finance healthz $c2 · /finance/approvals without a login $c3 · cn-detail without a login $c4 (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ] || [ "$c4" = 403 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[10/10] clinic-finance active, healthz 200, nothing 'NOT mounted'"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
for f in "${NEWF[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/approvals (Returns: counter vs your non-cash; the Month table's returns %)"
