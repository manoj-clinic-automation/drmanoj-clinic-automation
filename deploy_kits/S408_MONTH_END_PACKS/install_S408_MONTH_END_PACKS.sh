#!/bin/bash
# =============================================================================
#  install_S408_MONTH_END_PACKS.sh · kit S408_MONTH_END_PACKS (session 283, 26-Sep-2026, D624) · OWNER: PARENT (clinic)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S408_MONTH_END_PACKS/install_S408_MONTH_END_PACKS.sh
#
#  THE OWNER (26-Sep-2026, his formal list): the accountant pack, automatic; every bank statement received by email, every month;
#  the card statements with the password removed; the electricity lines; the Sanjeevni NEFT details; the payment digest; the scanned
#  bill bundles. Amir's pack pushed in his app. Shavez's monthly checklist as a page. Nothing manual changes until he sees the first pack.
#
#  NEW:    /root/finance/packs.py + packs.html + packs_checklist.html · stmt_shelf.py (the venv fetcher, cron 05:40) · finance_icici.py
#  PATCHED ON THE BOX from the live bytes (make_s408.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/finance_app.py            d19c2046 -> 5d9f2703   the unit 'packs' + the guarded mount
#          /root/portal/portal.py                  968ca602 -> 912a1d82   two tiles
#          /root/portal/tile_grants.json           0aadfc52 -> df73b84a   v28 -> v29 ('Mahine ka kaam' to shavez)
#          /root/finance/sanjeevni_approvals.py    f6fc90d5 -> 3cde91fb   two Needs-you lines after the 10th
#          /root/finance/amir_day.py               59a51d47 -> 068a3988   'Pichle mahine ka pack' on his board
#  ONE root cron line (05:40 IST) for stmt_shelf.py, declared; the crontab is backed up first.
#  Restarts clinic-finance + clinic-portal. finance.db backed up first; the seed adds the packs unit, two roles, three settings, the slots,
#  the checklist items; the accountants' addresses are read from the filer script in the repository clone, never typed here.
#  The walk (this kit's), then S409's, S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files.
# =============================================================================
set -u
KIT="S408_MONTH_END_PACKS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
K400="$(cd "$KDIR/../S400_MEDICAL_SALE_CHECK" 2>/dev/null && pwd)"
K402="$(cd "$KDIR/../S402_SALECHECK_RETURNS" 2>/dev/null && pwd)"
K403="$(cd "$KDIR/../S403_PURCHASE_ORDERS_LIVE" 2>/dev/null && pwd)"
K404="$(cd "$KDIR/../S404_ORTHO_STOCK_CLOSE" 2>/dev/null && pwd)"
K405="$(cd "$KDIR/../S405_BANK_SMS_DOOR" 2>/dev/null && pwd)"
K406="$(cd "$KDIR/../S406_RETURNS_TWO_KINDS" 2>/dev/null && pwd)"
K407="$(cd "$KDIR/../S407_NEFT_MESSAGES" 2>/dev/null && pwd)"
K409="$(cd "$KDIR/../S409_SCAN_LANES" 2>/dev/null && pwd)"
GAS="$KDIR/../GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s408_walk_$STAMP"
CRON_LINE="40 5 * * * cd $FIN && FINANCE_DB=$DBF $VPY -B $FIN/stmt_shelf.py run >> $FIN/stmt_shelf.log 2>&1 # S408_MONTH_END_PACKS"
declare -A FROM=( [finance_app.py]=d19c2046b190a4ec00745dc4121152e8 [portal.py]=968ca6027ae30d67e7d18b83f35b395d [tile_grants.json]=0aadfc523f9ab9c59633dedcd618cee9
                  [sanjeevni_approvals.py]=f6fc90d5d31badd3c5eec3691a78c4fb [amir_day.py]=59a51d471cb30702dfd0cb8b6b6f3a44 )
declare -A TO=( [finance_app.py]=5d9f2703b0142950fa2a0ee56c5938bd [portal.py]=912a1d8299c01b1b11f4ca81bef52482 [tile_grants.json]=df73b84a0bde3917b97c233647ffe0a5
                [sanjeevni_approvals.py]=3cde91fbfead8e698ca1e3981362a6d3 [amir_day.py]=068a3988e296f6579e2e780b2e4f623b )
declare -A DEST=( [finance_app.py]="$FIN/finance_app.py" [portal.py]="$POR/portal.py" [tile_grants.json]="$POR/tile_grants.json"
                  [sanjeevni_approvals.py]="$FIN/sanjeevni_approvals.py" [amir_day.py]="$FIN/amir_day.py" )
ORDER=(finance_app.py portal.py tile_grants.json sanjeevni_approvals.py amir_day.py)
NEWF=(packs.py packs.html packs_checklist.html stmt_shelf.py finance_icici.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K400" "$K402" "$K403" "$K404" "$K405" "$K406" "$K407" "$K409" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K400/walk_s400.py" "$K400/seed_s400.py" "$K402/walk_s402.py" "$K403/walk_s403.py" "$K403/seed_s403.py" "$K404/walk_s404.py" "$K404/seed_s404.py" "$K405/walk_s405.py" "$K405/seed_s405.py" "$K406/walk_s406.py" "$K406/seed_s406.py" "$K407/walk_s407.py" "$K407/seed_s407.py" "$K409/walk_s409.py" "$K409/seed_s409.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must sit beside this kit (the earlier walks re-run) - nothing installed"; exit 1; }
done
[ -f "$GAS" ] || { say "!! [1/10] the filer script $GAS is not beside this kit (the accountants' addresses are read from it) - nothing installed"; exit 1; }
for t in pdftotext pdfunite pdfinfo convert; do command -v "$t" >/dev/null 2>&1 || { say "!! [1/10] $t is not on the box; nothing installed"; exit 1; }; done
"$SPY" -c "import openpyxl" 2>/dev/null || { say "!! [1/10] openpyxl is missing on the app's python; nothing installed"; exit 1; }
say "[1/10] kit gates green (S400-S409 walks found; the filer script; pdftotext/pdfunite/pdfinfo/convert; openpyxl)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED. Seed re-checked:"; FINANCE_DIR="$FIN" "$SPY" -B seed_s408.py "$DBF" --gas "$GAS"; crontab -l 2>/dev/null | grep -q "S408_MONTH_END_PACKS" && say "   cron line present" || say "   !! cron line MISSING"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/10] ${DEST[$f]} is $(m5 "${DEST[$f]}"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] every live file at its FROM pin"
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" "$WALK/old409/finance_ui" "$WALK/old409/spine" "$WALK/old407/finance_ui" "$WALK/old407/spine" \
         "$WALK/old406/finance_ui" "$WALK/old406/spine" "$WALK/old405/finance_ui" "$WALK/old405/spine" "$WALK/old404/finance_ui" "$WALK/old404/spine" "$WALK/old403/finance_ui" "$WALK/old403/spine" \
         "$WALK/old0/finance_ui" "$WALK/old2/finance_ui" "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/assetapp_live" "$WALK/assetapp_old9" "$WALK/assetapp_old3" \
         "$WALK/pnew" "$WALK/plive" "$WALK/p403" "$WALK/p404" "$WALK/pold" "$WALK/uploads" "$WALK/stub" || exit 1
"$SPY" -B make_s408.py --finance "$FIN" --portal "$POR" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/10] live bytes + anchored edits give exactly the kit's five files (pins match)"
PYS="$WALK/built/finance_app.py $WALK/built/portal.py $WALK/built/sanjeevni_approvals.py $WALK/built/amir_day.py"
( "$SPY" -m py_compile packs.py stmt_shelf.py finance_icici.py seed_s408.py make_s408.py walk_s408.py $PYS 2>/dev/null && "$VPY" -m py_compile packs.py stmt_shelf.py finance_icici.py seed_s408.py $PYS 2>/dev/null \
  && "$VPY" -c "import json,sys; assert json.load(open(sys.argv[1],encoding='utf-8'))['version']==29" "$WALK/built/tile_grants.json" ) \
  || { say "!! [4/10] compile on both pythons / json failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python; grants v29"
for side in finance old old409 old407 old406 old405 old404 old403 old0 old2; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
done
for side in finance old old409 old407 old406 old405 old404 old403; do cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; done
[ -f "$FIN/spine/spine.db" ] && for side in finance old old409 old407 old406 old405 old403; do cp -p "$FIN/spine/spine.db" "$WALK/$side/spine/"; done
cp -p "$WALK/built/finance_app.py" "$WALK/built/sanjeevni_approvals.py" "$WALK/built/amir_day.py" "$WALK/finance/"
cp -p packs.py packs.html packs_checklist.html stmt_shelf.py finance_icici.py "$WALK/finance/"
for side in assetapp_live assetapp_old9 assetapp_old3; do cp -p "$AST"/*.py "$AST"/*.js "$WALK/$side/" 2>/dev/null; done
cp -p "$AST/asset_register.py.bak_S409_30b26d28" "$WALK/assetapp_old9/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S409_30b26d28 missing"; rm -rf "$WALK"; exit 1; }
cp -p "$AST/asset_register.py.bak_S403_71bd3277" "$WALK/assetapp_old3/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S403_71bd3277 missing"; rm -rf "$WALK"; exit 1; }
# old409 = before S409
for pair in "purchase_app.py:fdec7ec0" "porders.py:78d1712a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S409_$h" "$WALK/old409/$f" || { say "!! [5/10] $f.bak_S409_$h missing - cannot rebuild the pre-S409 control"; rm -rf "$WALK"; exit 1; }
done
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
# the portals: new (this kit, v29) · live (v28) · before S403 (v27) · before S404 · before S400
cp -p "$POR"/*.py "$WALK/pnew/"; cp -p "$WALK/built/portal.py" "$WALK/built/tile_grants.json" "$WALK/pnew/"
cp -p "$POR"/*.py "$WALK/plive/"; cp -p "$POR/tile_grants.json" "$WALK/plive/"
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p404/"; cp -p "$POR/portal.py.bak_S404_592ccf99" "$WALK/p404/portal.py"; cp -p "$POR/tile_grants.json.bak_S404_9231cefa" "$WALK/p404/tile_grants.json"
cp -p "$POR"/*.py "$WALK/pold/"; cp -p "$POR/portal.py.bak_S400_80d6dc44" "$WALK/pold/portal.py"; cp -p "$POR/tile_grants.json.bak_S400_7d195476" "$WALK/pold/tile_grants.json"
for i in 1 2 3 4 5 6 7 8 9; do copydb "$DBF" "$WALK/scratch$i.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }; done
for i in 1 2 3; do copydb "$ADB" "$WALK/assets_scratch$i.db" || { say "!! [5/10] no scratch copy of assets.db - nothing installed"; rm -rf "$WALK"; exit 1; }; done
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 1200 "$VPY" -B "$KDIR/walk_s408.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" \
         --assets-db "$WALK/assets_scratch1.db" --portal-new "$WALK/pnew" --portal-old "$WALK/plive" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S408 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s408 green on scratch copies of both live databases (above)"
W409="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch2.db" timeout 900 "$VPY" -B "$K409/walk_s409.py" --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old9" \
         --assets-db "$WALK/assets_scratch2.db" --app "$WALK/finance" --old "$WALK/old409" --db "$WALK/scratch2.db" 2>&1 )"
echo "$W409" | grep -E '^(WALK_S409|  FAIL|-- )' | sed 's/^/   /'
echo "$W409" | grep -q "^WALK_S409 GREEN" || { say "!! [6/10] S409's walk went red on the patched files - nothing installed"; echo "$W409" | tail -20; clean; rm -rf "$WALK"; exit 1; }
# S407's negative control asks the pre-S407 copy to have no supplier_msg table; the live database has grown it since (the pay page and
# Amir's board create it on first use), so the SCRATCH copy handed to S407's walk drops it first -- the walk's own rows rebuild it.
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('DROP TABLE IF EXISTS supplier_msg'); c.commit(); c.close()" "$WALK/scratch3.db"
W407="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch3.db" timeout 900 "$VPY" -B "$K407/walk_s407.py" --app "$WALK/finance" --old "$WALK/old407" --db "$WALK/scratch3.db" 2>&1 )"
echo "$W407" | grep -E '^(WALK_S407|  FAIL|-- )' | sed 's/^/   /'
echo "$W407" | grep -q "^WALK_S407 GREEN" || { say "!! [6/10] S407's walk went red on the patched files - nothing installed"; echo "$W407" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W406="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch4.db" timeout 900 "$VPY" -B "$K406/walk_s406.py" --app "$WALK/finance" --old "$WALK/old406" --db "$WALK/scratch4.db" 2>&1 )"
echo "$W406" | grep -E '^(WALK_S406|  FAIL|-- )' | sed 's/^/   /'
echo "$W406" | grep -q "^WALK_S406 GREEN" || { say "!! [6/10] S406's walk went red on the patched files - nothing installed"; echo "$W406" | tail -20; clean; rm -rf "$WALK"; exit 1; }
# the same for S405: its negative control wants no purchase_neft_event / bank_sms_* table in the pre-S405 copy; the live one grew
# purchase_neft_event through S407's pay page since. Dropped from the SCRATCH copy only; S405's own rows rebuild them.
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('purchase_neft_event','bank_sms_ignored','bank_sms_yes')]; c.commit(); c.close()" "$WALK/scratch5.db"
W405="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch5.db" timeout 900 "$VPY" -B "$K405/walk_s405.py" --app "$WALK/finance" --old "$WALK/old405" --db "$WALK/scratch5.db" 2>&1 )"
echo "$W405" | grep -E '^(WALK_S405|  FAIL|-- )' | sed 's/^/   /'
echo "$W405" | grep -q "^WALK_S405 GREEN" || { say "!! [6/10] S405's walk went red on the patched files - nothing installed"; echo "$W405" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W404="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch6.db" timeout 1500 "$VPY" -B "$K404/walk_s404.py" --app "$WALK/finance" --old "$WALK/old404" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch6.db" --portal-new "$WALK/p403" --portal-old "$WALK/p404" 2>&1 )"
echo "$W404" | grep -E '^(WALK_S404|  FAIL|-- )' | sed 's/^/   /'
echo "$W404" | grep -q "^WALK_S404 GREEN" || { say "!! [6/10] S404's walk went red on the patched files - nothing installed"; echo "$W404" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W403="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch7.db" timeout 1500 "$VPY" -B "$K403/walk_s403.py" --app "$WALK/finance" --old "$WALK/old403" \
         --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old3" --db "$WALK/scratch7.db" --assets-db "$WALK/assets_scratch3.db" \
         --portal-new "$WALK/plive" --portal-old "$WALK/p403" 2>&1 )"
echo "$W403" | grep -E '^(WALK_S403|  FAIL|-- )' | sed 's/^/   /'
echo "$W403" | grep -q "^WALK_S403 GREEN" || { say "!! [6/10] S403's walk went red on the patched files - nothing installed"; echo "$W403" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W400="$( cd "$WALK" && env $WENV NEEDS_YOU_WITHOUT_S403=1 NEEDS_YOU_WITHOUT_S406=1 NEEDS_YOU_WITHOUT_S408=1 FINANCE_DB="$WALK/scratch8.db" timeout 900 "$VPY" -B "$K400/walk_s400.py" --app "$WALK/finance" --old "$WALK/old0" --db "$WALK/scratch8.db" --portal-new "$WALK/p404" --portal-old "$WALK/pold" 2>&1 )"
echo "$W400" | grep -E '^(WALK_S400|  FAIL|-- )' | sed 's/^/   /'
echo "$W400" | grep -q "^WALK_S400 GREEN" || { say "!! [6/10] S400's walk went red on the patched files - nothing installed"; echo "$W400" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W402="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch9.db" timeout 900 "$VPY" -B "$K402/walk_s402.py" --app "$WALK/finance" --old "$WALK/old2" --db "$WALK/scratch9.db" 2>&1 )"
echo "$W402" | grep -E '^(WALK_S402|  FAIL|-- )' | sed 's/^/   /'
echo "$W402" | grep -q "^WALK_S402 GREEN" || { say "!! [6/10] S402's walk went red on the patched files - nothing installed"; echo "$W402" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S409's, S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files: still green (above)"
copydb "$DBF" "$FIN/finance.db.bak_S408_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
crontab -l > "$FIN/crontab.bak_S408_$STAMP" 2>/dev/null || true
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S408_$(m5 "${DEST[$f]}" | cut -c1-8)"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S408_$STAMP and crontab.bak_S408_$STAMP made; .bak_S408_<from8> beside each of the five files"
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  for f in "${NEWF[@]}"; do rm -f "$FIN/$f"; done
  crontab -l 2>/dev/null | grep -v "S408_MONTH_END_PACKS" | crontab - 2>/dev/null || true
  systemctl restart clinic-finance clinic-portal || true; sleep 4
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S408_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
mkdir -p "$FIN/statements/inbox" "$FIN/statements/packs" || restore
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "${DEST[$f]}" || restore; done
for f in "${NEWF[@]}"; do \cp -p "$f" "$FIN/$f" && chmod 644 "$FIN/$f" || restore; done
chmod 755 "$FIN/stmt_shelf.py" || restore
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
for f in "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || restore; done
say "[8/10] placed; every md5 read back = the kit's pin"
FINANCE_DIR="$FIN" "$SPY" -B seed_s408.py "$DBF" --gas "$GAS" || restore
( crontab -l 2>/dev/null | grep -v "S408_MONTH_END_PACKS"; echo "$CRON_LINE" ) | crontab - || restore
crontab -l | grep -q "S408_MONTH_END_PACKS" || restore
say "[9/10] packs unit, settings, slots and checklist seeded; the accountants' addresses read from the filer script; the 05:40 cron line placed"
systemctl restart clinic-finance || restore
systemctl restart clinic-portal || restore
sleep 6
for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || restore; done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/packs)
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/packs/checklist)
say "health : finance healthz $c2 · portal $c3 · /finance/packs without a login $c4 · /finance/packs/checklist $c5 (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c3" = 200 ] || [ "$c3" = 302 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } && { [ "$c5" = 302 ] || [ "$c5" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[10/10] clinic-finance + clinic-portal active, healthz 200, nothing 'NOT mounted'"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
for f in "${NEWF[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/packs · https://followup.dr-manoj.in/finance/packs/checklist · https://followup.dr-manoj.in/finance/amir"
