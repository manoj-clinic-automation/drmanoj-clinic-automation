#!/bin/bash
# =============================================================================
#  install_S410_MEDICINE_ORDERING.sh · kit S410_MEDICINE_ORDERING (session 283, 26-Sep-2026, D626) · Sanjeevni
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S410_MEDICINE_ORDERING/install_S410_MEDICINE_ORDERING.sh
#
#  THE OWNER (26-Sep-2026, D626): the medicine buying rules as settings on his page; fixed order days (Kedar Mon + Fri, Thursday open);
#  the ordering team's day prepared at 09:00 with reminders at 12 / 15 / 17; interim orders; his Needs you only for a stuck order,
#  a month above pace and the Kedar review; the paper purchase-order sheet retired -- the system's record replaces it.
#
#  NEW:    /root/finance/order_rules.py (the settings, the engine wrapper, the calendar, the day scheduler, the notices, the two blocks)
#  PATCHED ON THE BOX from the live bytes (make_s410.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/porders.py                        d08f59e2 -> c75fc910   mounts order_rules; state() carries today; the freeze gate
#          /root/finance/porders.html                      76a173af -> 5913e993   section 4 "Aaj ke order (N)"; section 5 the holidays
#          /root/finance/sanjeevni_approvals.py            3cde91fb -> c5b93455   v1.10: the Needs-you lines
#          /root/finance/finance_ui/finance_approvals.html 77c79211 -> 7de58315   the red bar, the rules fold, New items, the review tap
#          /root/finance/darpan_kal.py                     401ee01c -> 803970bd   the count line in the payload
#          /root/finance/darpan_kal.html                   1bedb469 -> a4eecb21   the count line on the card
#  ONE root cron line (every half hour 05:00-17:30; the worker acts at 05:30 · 09:00 · 12:00 · 15:00 · 17:00), declared; crontab backed up.
#  Restarts clinic-finance ONLY. finance.db backed up first; the seed adds the order.* settings and one rule row per supplier.
#  The walk (this kit's), then S409's, S408's, S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files.
# =============================================================================
set -u
KIT="S410_MEDICINE_ORDERING"
KDIR="$(cd "$(dirname "$0")" && pwd)"
K400="$(cd "$KDIR/../S400_MEDICAL_SALE_CHECK" 2>/dev/null && pwd)"
K402="$(cd "$KDIR/../S402_SALECHECK_RETURNS" 2>/dev/null && pwd)"
K403="$(cd "$KDIR/../S403_PURCHASE_ORDERS_LIVE" 2>/dev/null && pwd)"
K404="$(cd "$KDIR/../S404_ORTHO_STOCK_CLOSE" 2>/dev/null && pwd)"
K405="$(cd "$KDIR/../S405_BANK_SMS_DOOR" 2>/dev/null && pwd)"
K406="$(cd "$KDIR/../S406_RETURNS_TWO_KINDS" 2>/dev/null && pwd)"
K407="$(cd "$KDIR/../S407_NEFT_MESSAGES" 2>/dev/null && pwd)"
K408="$(cd "$KDIR/../S408_MONTH_END_PACKS" 2>/dev/null && pwd)"
K409="$(cd "$KDIR/../S409_SCAN_LANES" 2>/dev/null && pwd)"
GAS="$KDIR/../GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s410_walk_$STAMP"
CRON_LINE="0,30 5-17 * * * cd $FIN && FINANCE_DB=$DBF $VPY -B $FIN/order_rules.py tick >> $FIN/order_rules.log 2>&1 # S410_MEDICINE_ORDERING"
declare -A FROM=( [porders.py]=d08f59e2fb4e42e173f135f06da28787 [porders.html]=76a173af5faee643fa0d0139731b10e8 [sanjeevni_approvals.py]=3cde91fbfead8e698ca1e3981362a6d3
                  [finance_approvals.html]=77c79211845f3416a3211d22ced3d7db [darpan_kal.py]=401ee01c7cbd49cea1c34665c99bab60 [darpan_kal.html]=1bedb46991bc5b531e809519c50ee990 )
declare -A TO=( [porders.py]=c75fc91060d127fd05c56b6b81ad9b97 [porders.html]=5913e99302930d9fae24c42ac630f010 [sanjeevni_approvals.py]=c5b93455a69083a6b8d634014898bd30
                [finance_approvals.html]=7de583154b87bd4d3ba13ce6de1c53a9 [darpan_kal.py]=803970bd04c7203632b98d9659923b3b [darpan_kal.html]=a4eecb21a88f793ab5c81b75dab20a51 )
declare -A DEST=( [porders.py]="$FIN/porders.py" [porders.html]="$FIN/porders.html" [sanjeevni_approvals.py]="$FIN/sanjeevni_approvals.py"
                  [finance_approvals.html]="$FIN/finance_ui/finance_approvals.html" [darpan_kal.py]="$FIN/darpan_kal.py" [darpan_kal.html]="$FIN/darpan_kal.html" )
ORDER=(porders.py porders.html sanjeevni_approvals.py finance_approvals.html darpan_kal.py darpan_kal.html)
NEWF=(order_rules.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K400" "$K402" "$K403" "$K404" "$K405" "$K406" "$K407" "$K408" "$K409" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K400/walk_s400.py" "$K400/seed_s400.py" "$K402/walk_s402.py" "$K403/walk_s403.py" "$K403/seed_s403.py" "$K404/walk_s404.py" "$K404/seed_s404.py" "$K405/walk_s405.py" "$K405/seed_s405.py" "$K406/walk_s406.py" "$K406/seed_s406.py" "$K407/walk_s407.py" "$K407/seed_s407.py" "$K408/walk_s408.py" "$K408/seed_s408.py" "$K409/walk_s409.py" "$K409/seed_s409.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must sit beside this kit (the earlier walks re-run) - nothing installed"; exit 1; }
done
[ -f "$GAS" ] || { say "!! [1/10] the filer script $GAS is not beside this kit (S408's walk reads it) - nothing installed"; exit 1; }
for t in pdftotext pdfunite pdfinfo convert pdftoppm; do command -v "$t" >/dev/null 2>&1 || { say "!! [1/10] $t is not on the box (the earlier walks need it); nothing installed"; exit 1; }; done
"$VPY" -c "import pywebpush, flask" 2>/dev/null || { say "!! [1/10] the venv python lacks pywebpush or flask (the cron worker needs both); nothing installed"; exit 1; }
[ -f "$POR/ring_common.py" ] || { say "!! [1/10] $POR/ring_common.py is missing (the push door); nothing installed"; exit 1; }
say "[1/10] kit gates green (S400-S409 walks found; the filer script; the PDF/image tools; pywebpush + flask on the venv; the push door)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
NEWOK=1; for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || NEWOK=0; done
if [ "$ALL" = 1 ] && [ "$NEWOK" = 1 ]; then say "-- ALREADY INSTALLED. Seed re-checked:"; FINANCE_DIR="$FIN" "$SPY" -B seed_s410.py "$DBF"; crontab -l 2>/dev/null | grep -q "S410_MEDICINE_ORDERING" && say "   cron line present" || say "   !! cron line MISSING"; exit 0; fi
# REFRESH: the six patched files already sit at their TO pins and only the kit's NEW module differs (a later revision of this same kit,
# before publication): the walks re-run with the kit's module against the pre-S410 control rebuilt from the .bak_S410 files; then only
# that module is backed up and re-placed. The six patched files are not touched again.
REFRESH=0
if [ "$ALL" = 1 ] && [ "$NEWOK" = 0 ]; then REFRESH=1; say "[2/10] REFRESH: the six patched files are at their pins; only ${NEWF[*]} differs from the kit -- the walks re-run, then it is re-placed"; fi
if [ "$REFRESH" = 0 ]; then
  for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/10] ${DEST[$f]} is $(m5 "${DEST[$f]}"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
  say "[2/10] every live file at its FROM pin"
fi
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" "$WALK/old409/finance_ui" "$WALK/old409/spine" "$WALK/old408/finance_ui" "$WALK/old408/spine" \
         "$WALK/old407/finance_ui" "$WALK/old407/spine" "$WALK/old406/finance_ui" "$WALK/old406/spine" "$WALK/old405/finance_ui" "$WALK/old405/spine" "$WALK/old404/finance_ui" "$WALK/old404/spine" \
         "$WALK/old403/finance_ui" "$WALK/old403/spine" "$WALK/old0/finance_ui" "$WALK/old2/finance_ui" "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/assetapp_live" "$WALK/assetapp_old9" "$WALK/assetapp_old3" \
         "$WALK/plive" "$WALK/p408" "$WALK/p403" "$WALK/p404" "$WALK/pold" "$WALK/uploads" "$WALK/stub" || exit 1
if [ "$REFRESH" = 0 ]; then
  "$SPY" -B make_s410.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
  for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
  say "[3/10] live bytes + anchored edits give exactly the kit's six files (pins match)"
else
  for f in "${ORDER[@]}"; do cp -p "${DEST[$f]}" "$WALK/built/$f"; done
  say "[3/10] refresh: the six patched files taken as they stand (at their pins)"
fi
PYS="$WALK/built/porders.py $WALK/built/sanjeevni_approvals.py $WALK/built/darpan_kal.py"
( "$SPY" -m py_compile order_rules.py seed_s410.py make_s410.py walk_s410.py $PYS 2>/dev/null && "$VPY" -m py_compile order_rules.py seed_s410.py $PYS 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in finance old old409 old408 old407 old406 old405 old404 old403 old0 old2; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
done
for side in finance old old409 old408 old407 old406 old405 old404 old403; do cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; done
[ -f "$FIN/spine/spine.db" ] && for side in finance old old409 old408 old407 old406 old405 old403; do cp -p "$FIN/spine/spine.db" "$WALK/$side/spine/"; done
if [ "$REFRESH" = 1 ]; then
  # every control dir is the box BEFORE S410: the six .bak_S410 files back, the module gone (then each kit's own older overlay below)
  for side in old old409 old408 old407 old406 old405 old404 old403 old0 old2; do
    for pair in "porders.py:d08f59e2" "porders.html:76a173af" "sanjeevni_approvals.py:3cde91fb" "darpan_kal.py:401ee01c" "darpan_kal.html:1bedb469"; do
      f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S410_$h" "$WALK/$side/$f" || { say "!! [5/10] $f.bak_S410_$h missing - cannot rebuild the pre-S410 control"; rm -rf "$WALK"; exit 1; }
    done
    cp -p "$FIN/finance_ui/finance_approvals.html.bak_S410_77c79211" "$WALK/$side/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
    rm -f "$WALK/$side/order_rules.py"
  done
fi
cp -p "$WALK/built/porders.py" "$WALK/built/porders.html" "$WALK/built/sanjeevni_approvals.py" "$WALK/built/darpan_kal.py" "$WALK/built/darpan_kal.html" "$WALK/finance/"
cp -p "$WALK/built/finance_approvals.html" "$WALK/finance/finance_ui/"
cp -p order_rules.py "$WALK/finance/"
for side in assetapp_live assetapp_old9 assetapp_old3; do cp -p "$AST"/*.py "$AST"/*.js "$WALK/$side/" 2>/dev/null; done
cp -p "$AST/asset_register.py.bak_S409_30b26d28" "$WALK/assetapp_old9/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S409_30b26d28 missing"; rm -rf "$WALK"; exit 1; }
cp -p "$AST/asset_register.py.bak_S403_71bd3277" "$WALK/assetapp_old3/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S403_71bd3277 missing"; rm -rf "$WALK"; exit 1; }
# old409 = before S409
for pair in "purchase_app.py:fdec7ec0" "porders.py:78d1712a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S409_$h" "$WALK/old409/$f" || { say "!! [5/10] $f.bak_S409_$h missing - cannot rebuild the pre-S409 control"; rm -rf "$WALK"; exit 1; }
done
# old408 = before S408
for pair in "finance_app.py:d19c2046" "sanjeevni_approvals.py:f6fc90d5" "amir_day.py:59a51d47"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S408_$h" "$WALK/old408/$f" || { say "!! [5/10] $f.bak_S408_$h missing - cannot rebuild the pre-S408 control"; rm -rf "$WALK"; exit 1; }
done
rm -f "$WALK/old408/packs.py" "$WALK/old408/packs.html" "$WALK/old408/packs_checklist.html" "$WALK/old408/stmt_shelf.py" "$WALK/old408/finance_icici.py"
# old407 = before S407
for pair in "purchase_app.py:7896eae4" "amir_day.py:00c443cb" "sanjeevni_approvals.py:74fe5437" "finance_app.py:8055b0de"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S407_$h" "$WALK/old407/$f" || { say "!! [5/10] $f.bak_S407_$h missing - cannot rebuild the pre-S407 control"; rm -rf "$WALK"; exit 1; }
done
rm -f "$WALK/old407/supplier_msg.py"
# old406 = before S406
for pair in "darpan_app.py:2c22822d" "sanjeevni_approvals.py:126f90fc"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S406_$h" "$WALK/old406/$f" || { say "!! [5/10] $f.bak_S406_$h missing - cannot rebuild the pre-S406 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S406_928a25ef" "$WALK/old406/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old406/returns_kinds.py"
# old405 = before S405
for pair in "bank_sms.py:3a8f0a88" "sanjeevni_approvals.py:675aab4a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S405_$h" "$WALK/old405/$f" || { say "!! [5/10] $f.bak_S405_$h missing - cannot rebuild the pre-S405 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S405_c319bb56" "$WALK/old405/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
# old404 = before S404
for pair in "stock_app.py:1b473fbf" "stock_hub.html:c4f3280b" "stock_amir.html:14024b8d" "section_map.py:b05b0f08" "finance_app.py:d7ee72c5"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S404_$h" "$WALK/old404/$f" || { say "!! [5/10] $f.bak_S404_$h missing - cannot rebuild the pre-S404 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/spine/spine_build.py.bak_S404_1378c87d" "$WALK/old404/spine/spine_build.py" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old404/item_alias.py" "$WALK/old404/stockmatch.py" "$WALK/old404/stockmatch.html"
for side in marg_ingest marg_old; do cp -p "$MRG"/*.py "$WALK/$side/" 2>/dev/null; cp -rp "$MRG/xlrd" "$WALK/$side/xlrd" 2>/dev/null; [ -d "$MRG/lib" ] && cp -rp "$MRG/lib" "$WALK/$side/lib"; done
cp -p "$MRG/marg_take.py.bak_S404_75b8056c" "$WALK/marg_old/marg_take.py" || { say "!! [5/10] marg_take.py.bak_S404_75b8056c missing"; rm -rf "$WALK"; exit 1; }
# old403 = before S403
for pair in "purchase_app.py:9ad50878" "darpan_kal.py:1958ee7c" "darpan_kal.html:4f115f44" "sale_check.py:92ca5cb2" "sale_check.html:9c70af26" "sanjeevni_approvals.py:5fdfa364" "finance_app.py:186a500a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S403_$h" "$WALK/old403/$f" || { say "!! [5/10] $f.bak_S403_$h missing - cannot rebuild the pre-S403 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S403_6622587e" "$WALK/old403/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old403/porders.py" "$WALK/old403/porders.html"
# old0 = before S400; old2 = before S402
for pair in "finance_app.py:70cff498" "sanjeevni_day.py:5d16eff5" "sanjeevni_approvals.py:7ab5fec6"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S400_$h" "$WALK/old0/$f" || { say "!! [5/10] $f.bak_S400_$h missing - cannot rebuild the pre-S400 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S400_750f89e0" "$WALK/old0/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old0/sale_check.py" "$WALK/old0/sale_check.html"
cp -p "$FIN/sale_check.py.bak_S402_81cccad3" "$WALK/old2/sale_check.py" && cp -p "$FIN/sale_check.html.bak_S402_4202d11b" "$WALK/old2/sale_check.html" || { say "!! [5/10] the .bak_S402 files are missing"; rm -rf "$WALK"; exit 1; }
# the portals: live (v29) · before S408 (v28 = what S403/S404 left: S403's walk reads it as its 'new') · before S403 (v27) · before S404 · before S400
cp -p "$POR"/*.py "$WALK/plive/"; cp -p "$POR/tile_grants.json" "$WALK/plive/"
cp -p "$POR"/*.py "$WALK/p408/"; cp -p "$POR/portal.py.bak_S408_968ca602" "$WALK/p408/portal.py"; cp -p "$POR/tile_grants.json.bak_S408_0aadfc52" "$WALK/p408/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p404/"; cp -p "$POR/portal.py.bak_S404_592ccf99" "$WALK/p404/portal.py"; cp -p "$POR/tile_grants.json.bak_S404_9231cefa" "$WALK/p404/tile_grants.json"
cp -p "$POR"/*.py "$WALK/pold/"; cp -p "$POR/portal.py.bak_S400_80d6dc44" "$WALK/pold/portal.py"; cp -p "$POR/tile_grants.json.bak_S400_7d195476" "$WALK/pold/tile_grants.json"
for i in 1 2 3 4 5 6 7 8 9 10; do copydb "$DBF" "$WALK/scratch$i.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }; done
for i in 1 2 3; do copydb "$ADB" "$WALK/assets_scratch$i.db" || { say "!! [5/10] no scratch copy of assets.db - nothing installed"; rm -rf "$WALK"; exit 1; }; done
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 1200 "$VPY" -B "$KDIR/walk_s410.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S410 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s410 green on a scratch copy of the live database (above)"
W409="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch2.db" timeout 900 "$VPY" -B "$K409/walk_s409.py" --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old9" \
         --assets-db "$WALK/assets_scratch2.db" --app "$WALK/finance" --old "$WALK/old409" --db "$WALK/scratch2.db" 2>&1 )"
echo "$W409" | grep -E '^(WALK_S409|  FAIL|-- )' | sed 's/^/   /'
echo "$W409" | grep -q "^WALK_S409 GREEN" || { say "!! [6/10] S409's walk went red on the patched files - nothing installed"; echo "$W409" | tail -20; clean; rm -rf "$WALK"; exit 1; }
# S408's frozen walk asks the pre-S408 copy to have no shelf tables and seeds its own slots; the live database has carried them since
# S408's install this morning. Dropped from the SCRATCH copy only -- S408's own seed rebuilds them inside its walk.
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('stmt_slot','stmt_file','pack_send','pack_tick','packs_item','packs_done')]; c.commit(); c.close()" "$WALK/scratch3.db"
W408="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch3.db" timeout 1200 "$VPY" -B "$K408/walk_s408.py" --app "$WALK/finance" --old "$WALK/old408" --db "$WALK/scratch3.db" \
         --assets-db "$WALK/assets_scratch1.db" --portal-new "$WALK/plive" --portal-old "$WALK/p408" 2>&1 )"
echo "$W408" | grep -E '^(WALK_S408|  FAIL|-- )' | sed 's/^/   /'
echo "$W408" | grep -q "^WALK_S408 GREEN" || { say "!! [6/10] S408's walk went red on the patched files - nothing installed"; echo "$W408" | tail -20; clean; rm -rf "$WALK"; exit 1; }
# S407's negative control wants no supplier_msg table in the pre-S407 copy; the live database has grown it (the pay page creates it on first use):
# dropped from the SCRATCH copy only -- the walk's own rows rebuild it. The same for S405 (purchase_neft_event / bank_sms_*).
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('DROP TABLE IF EXISTS supplier_msg'); c.commit(); c.close()" "$WALK/scratch4.db"
W407="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch4.db" timeout 900 "$VPY" -B "$K407/walk_s407.py" --app "$WALK/finance" --old "$WALK/old407" --db "$WALK/scratch4.db" 2>&1 )"
echo "$W407" | grep -E '^(WALK_S407|  FAIL|-- )' | sed 's/^/   /'
echo "$W407" | grep -q "^WALK_S407 GREEN" || { say "!! [6/10] S407's walk went red on the patched files - nothing installed"; echo "$W407" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W406="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch5.db" timeout 900 "$VPY" -B "$K406/walk_s406.py" --app "$WALK/finance" --old "$WALK/old406" --db "$WALK/scratch5.db" 2>&1 )"
echo "$W406" | grep -E '^(WALK_S406|  FAIL|-- )' | sed 's/^/   /'
echo "$W406" | grep -q "^WALK_S406 GREEN" || { say "!! [6/10] S406's walk went red on the patched files - nothing installed"; echo "$W406" | tail -20; clean; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('purchase_neft_event','bank_sms_ignored','bank_sms_yes')]; c.commit(); c.close()" "$WALK/scratch6.db"
W405="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch6.db" timeout 900 "$VPY" -B "$K405/walk_s405.py" --app "$WALK/finance" --old "$WALK/old405" --db "$WALK/scratch6.db" 2>&1 )"
echo "$W405" | grep -E '^(WALK_S405|  FAIL|-- )' | sed 's/^/   /'
echo "$W405" | grep -q "^WALK_S405 GREEN" || { say "!! [6/10] S405's walk went red on the patched files - nothing installed"; echo "$W405" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W404="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch7.db" timeout 1500 "$VPY" -B "$K404/walk_s404.py" --app "$WALK/finance" --old "$WALK/old404" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch7.db" --portal-new "$WALK/p403" --portal-old "$WALK/p404" 2>&1 )"
echo "$W404" | grep -E '^(WALK_S404|  FAIL|-- )' | sed 's/^/   /'
echo "$W404" | grep -q "^WALK_S404 GREEN" || { say "!! [6/10] S404's walk went red on the patched files - nothing installed"; echo "$W404" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W403="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch8.db" timeout 1500 "$VPY" -B "$K403/walk_s403.py" --app "$WALK/finance" --old "$WALK/old403" \
         --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old3" --db "$WALK/scratch8.db" --assets-db "$WALK/assets_scratch3.db" \
         --portal-new "$WALK/p408" --portal-old "$WALK/p403" 2>&1 )"
echo "$W403" | grep -E '^(WALK_S403|  FAIL|-- )' | sed 's/^/   /'
echo "$W403" | grep -q "^WALK_S403 GREEN" || { say "!! [6/10] S403's walk went red on the patched files - nothing installed"; echo "$W403" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W400="$( cd "$WALK" && env $WENV NEEDS_YOU_WITHOUT_S403=1 NEEDS_YOU_WITHOUT_S406=1 NEEDS_YOU_WITHOUT_S408=1 NEEDS_YOU_WITHOUT_S410=1 FINANCE_DB="$WALK/scratch9.db" timeout 900 "$VPY" -B "$K400/walk_s400.py" --app "$WALK/finance" --old "$WALK/old0" --db "$WALK/scratch9.db" --portal-new "$WALK/p404" --portal-old "$WALK/pold" 2>&1 )"
echo "$W400" | grep -E '^(WALK_S400|  FAIL|-- )' | sed 's/^/   /'
echo "$W400" | grep -q "^WALK_S400 GREEN" || { say "!! [6/10] S400's walk went red on the patched files - nothing installed"; echo "$W400" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W402="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch10.db" timeout 900 "$VPY" -B "$K402/walk_s402.py" --app "$WALK/finance" --old "$WALK/old2" --db "$WALK/scratch10.db" 2>&1 )"
echo "$W402" | grep -E '^(WALK_S402|  FAIL|-- )' | sed 's/^/   /'
echo "$W402" | grep -q "^WALK_S402 GREEN" || { say "!! [6/10] S402's walk went red on the patched files - nothing installed"; echo "$W402" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S409's, S408's, S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files: still green (above)"
copydb "$DBF" "$FIN/finance.db.bak_S410_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
crontab -l > "$FIN/crontab.bak_S410_$STAMP" 2>/dev/null || true
declare -A BAK
declare -A NEWBAK
if [ "$REFRESH" = 0 ]; then
  for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S410_$(m5 "${DEST[$f]}" | cut -c1-8)"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
  say "[7/10] finance.db.bak_S410_$STAMP and crontab.bak_S410_$STAMP made; .bak_S410_<from8> beside each of the six files"
else
  for f in "${NEWF[@]}"; do NEWBAK[$f]="$FIN/$f.bak_S410_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${NEWBAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
  say "[7/10] refresh: finance.db.bak_S410_$STAMP and crontab.bak_S410_$STAMP made; ${NEWF[*]} backed up beside itself (.bak_S410_<md5-8>)"
fi
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  if [ "$REFRESH" = 0 ]; then
    for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
    for f in "${NEWF[@]}"; do rm -f "$FIN/$f"; done
    crontab -l 2>/dev/null | grep -v "S410_MEDICINE_ORDERING" | crontab - 2>/dev/null || true
  else
    for f in "${NEWF[@]}"; do \cp -p "${NEWBAK[$f]}" "$FIN/$f"; done
  fi
  systemctl restart clinic-finance || true; sleep 4
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  for f in "${NEWF[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S410_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
if [ "$REFRESH" = 0 ]; then for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "${DEST[$f]}" || restore; done; fi
for f in "${NEWF[@]}"; do \cp -p "$f" "$FIN/$f" && chmod 644 "$FIN/$f" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || restore; done
say "[8/10] placed; every md5 read back = the kit's pin"
FINANCE_DIR="$FIN" "$SPY" -B seed_s410.py "$DBF" || restore
( crontab -l 2>/dev/null | grep -v "S410_MEDICINE_ORDERING"; echo "$CRON_LINE" ) | crontab - || restore
crontab -l | grep -q "S410_MEDICINE_ORDERING" || restore
say "[9/10] order.* settings and the supplier rules seeded (Kedar's D626 row); the cron line placed"
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/porders)
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/porders/api/rules/state)
say "health : finance healthz $c2 · /finance/porders without a login $c4 · the rules state without a login $c5 (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } && { [ "$c5" = 302 ] || [ "$c5" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B "$FIN/order_rules.py" status | sed 's/^/   status: /' || restore
cd "$KDIR"
say "[10/10] clinic-finance active, healthz 200, nothing 'NOT mounted', the worker answers"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
for f in "${NEWF[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/approvals · https://followup.dr-manoj.in/finance/porders"
