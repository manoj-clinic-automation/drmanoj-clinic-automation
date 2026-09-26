#!/bin/bash
# =============================================================================
#  install_S417_DAY_ONE_FIXES.sh · kit S417_DAY_ONE_FIXES (session 283, 26-Sep-2026, F-636) · Sanjeevni + PARENT pieces (declared)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S417_DAY_ONE_FIXES/install_S417_DAY_ONE_FIXES.sh
#
#  FOUR CORRECTIONS FROM THE OWNER'S FIRST DAY ON S403-S414:
#   1  the stock beside an order in the order's own unit ('12 strips + 4', '3 pcs', '3 bottles', '5 units') on /page/orders, /page/staff,
#      the Purchase orders screen and the owner's section; the WhatsApp text untouched.
#   2  the card shelf: the card statements READ (statement date, period, card number) from the decrypted PDF; the month cells and pack
#      row 4 fill; the slot learns the card number(s); 'duplicate of decrypted' / 'decrypted copy not yet made'; the running Excel in the
#      Credit Card Statements root is all_txn, never 'which account?'.
#   3  the Yes Bank tile: a provisional NEFT (owner-tapped / SMS-confirmed, not yet on a statement) is its own line under the balance and
#      the headline is net of it, 'incl. provisional'; gone the moment the statement confirms it. Read-only.
#   4  the JIARDIANCE name search -- facts only, printed in this log, nothing changed.
#
#  PATCHED ON THE BOX from the live bytes (make_s417.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/purchase_app.py                     cdd4e9c0 -> 9c40d13e   stock_text; /page/orders, /page/staff, _staff_plan
#          /root/finance/porders.py                          c75fc910 -> 64465af0   stock_text on the plan and the proposals; shelf_text
#          /root/finance/porders.html                        5913e993 -> 124c4d41   sections 1 and 4 print the words
#          /root/finance/finance_ui/finance_approvals.html   eba564a4 -> 588975fc   owner's orthotic shelf in pieces; the Yes Bank tile line (clinic file, declared)
#          /root/finance/sanjeevni_approvals.py              c5b93455 -> 64548b9b   provisional_nefts + the tile's figures
#          /root/finance/packs.py                            359403f7 -> 938aa68f   the card reader, the months, the twins, the Excel (clinic file, declared)
#          /root/finance/stmt_shelf.py                       94f456ce -> 95ba0a4f   the cards-root .xlsx fetched as all_txn (clinic file, declared)
#  DATA: seed_s417.py on the live database AFTER the backup -- the card files re-read (the bank rows untouched). Restarts clinic-finance
#  ONLY. The walk (this kit's), then S414's, S412's, S411's, S410's, S409's, S408's (26/27 + the S411-declared supersession), S407's,
#  S406's, S405's, S404's (on the 14:04 backup, as S414 ran it), S403's and S400's (on the 17:45 backup S414's install took -- the owner
#  approved the rules and tapped NEFT after it; declared) and S402's own walks re-run on the patched files, with the scratch pre-states
#  S414's installer declared.
# =============================================================================
set -u
KIT="S417_DAY_ONE_FIXES"
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
K410="$(cd "$KDIR/../S410_MEDICINE_ORDERING" 2>/dev/null && pwd)"
K411="$(cd "$KDIR/../S411_SHELF_FIRST_RUN" 2>/dev/null && pwd)"
K412="$(cd "$KDIR/../S412_YESBANK_UNLOCK" 2>/dev/null && pwd)"
K414="$(cd "$KDIR/../S414_RULES_PAGE_UX" 2>/dev/null && pwd)"
GAS="$KDIR/../GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s417_walk_$STAMP"
S408_SUPERSEDED="the ICICI reader read the fixture into bank_statement_period/_line"
S411_BAK="$FIN/finance.db.bak_S411_20260926_124432"
S412_BAK="$FIN/finance.db.bak_S412_20260926_140429"
declare -A FROM=( [purchase_app.py]=cdd4e9c069bc8ab78160349a11a4a4c7 [porders.py]=c75fc91060d127fd05c56b6b81ad9b97 [porders.html]=5913e99302930d9fae24c42ac630f010
                  [finance_approvals.html]=eba564a425c1fc844f1d8d975a1d5eca [sanjeevni_approvals.py]=c5b93455a69083a6b8d634014898bd30
                  [packs.py]=359403f792eaafad37d4eeac3f762641 [stmt_shelf.py]=94f456ce0a6f469ecd7d3f16ca1e874e )
declare -A TO=( [purchase_app.py]=9c40d13ed222addeadf97d3f352f359a [porders.py]=64465af0835bdc5583ae7468cacc8c16 [porders.html]=124c4d41b9491203899f324b8a194763
                [finance_approvals.html]=588975fcff2644db115b63058c4d62dc [sanjeevni_approvals.py]=64548b9b36770992dd3da2081e52ffe1
                [packs.py]=938aa68fbe064b5025768ecfbff89897 [stmt_shelf.py]=95ba0a4fadd25d9f30a67e7f99eba9f1 )
declare -A DEST=( [purchase_app.py]="$FIN/purchase_app.py" [porders.py]="$FIN/porders.py" [porders.html]="$FIN/porders.html"
                  [finance_approvals.html]="$FIN/finance_ui/finance_approvals.html" [sanjeevni_approvals.py]="$FIN/sanjeevni_approvals.py"
                  [packs.py]="$FIN/packs.py" [stmt_shelf.py]="$FIN/stmt_shelf.py" )
ORDER=(purchase_app.py porders.py porders.html finance_approvals.html sanjeevni_approvals.py packs.py stmt_shelf.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K400" "$K402" "$K403" "$K404" "$K405" "$K406" "$K407" "$K408" "$K409" "$K410" "$K411" "$K412" "$K414" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K400/walk_s400.py" "$K400/seed_s400.py" "$K402/walk_s402.py" "$K403/walk_s403.py" "$K403/seed_s403.py" "$K404/walk_s404.py" "$K404/seed_s404.py" "$K405/walk_s405.py" "$K405/seed_s405.py" "$K406/walk_s406.py" "$K406/seed_s406.py" "$K407/walk_s407.py" "$K407/seed_s407.py" "$K408/walk_s408.py" "$K408/seed_s408.py" "$K409/walk_s409.py" "$K409/seed_s409.py" "$K410/walk_s410.py" "$K410/seed_s410.py" "$K411/walk_s411.py" "$K411/seed_s411.py" "$K412/walk_s412.py" "$K412/seed_s412.py" "$K414/walk_s414.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must sit beside this kit (the earlier walks re-run) - nothing installed"; exit 1; }
done
[ -f "$GAS" ] || { say "!! [1/10] the filer script $GAS is not beside this kit (S408's walk reads it) - nothing installed"; exit 1; }
for t in pdftotext pdfunite pdfinfo convert pdftoppm; do command -v "$t" >/dev/null 2>&1 || { say "!! [1/10] $t is not on the box (the walks need it); nothing installed"; exit 1; }; done
"$VPY" -c "import pywebpush, flask, pypdf, openpyxl" 2>/dev/null || { say "!! [1/10] the venv python lacks pywebpush / flask / pypdf / openpyxl (the walks need them); nothing installed"; exit 1; }
say "[1/10] kit gates green (S400-S414 walks found; the filer script; the PDF/image tools; the venv modules)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the seven files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance); healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/10] ${DEST[$f]} is $(m5 "${DEST[$f]}"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] all seven live files at their FROM pins"
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" "$WALK/old414/finance_ui" "$WALK/old414/spine" "$WALK/old412/finance_ui" "$WALK/old412/spine" "$WALK/old411/finance_ui" "$WALK/old411/spine" "$WALK/old410/finance_ui" "$WALK/old410/spine" "$WALK/old409/finance_ui" "$WALK/old409/spine" "$WALK/old408/finance_ui" "$WALK/old408/spine" \
         "$WALK/old407/finance_ui" "$WALK/old407/spine" "$WALK/old406/finance_ui" "$WALK/old406/spine" "$WALK/old405/finance_ui" "$WALK/old405/spine" "$WALK/old404/finance_ui" "$WALK/old404/spine" \
         "$WALK/old403/finance_ui" "$WALK/old403/spine" "$WALK/old0/finance_ui" "$WALK/old2/finance_ui" "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/assetapp_live" "$WALK/assetapp_old9" "$WALK/assetapp_old3" \
         "$WALK/plive" "$WALK/p408" "$WALK/p403" "$WALK/p404" "$WALK/pold" "$WALK/uploads" "$WALK/stub" || exit 1
"$SPY" -B make_s417.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/10] live bytes + anchored edits give exactly the kit's seven files (pins match)"
( "$SPY" -m py_compile make_s417.py walk_s417.py seed_s417.py name_search_s417.py "$WALK/built/purchase_app.py" "$WALK/built/porders.py" "$WALK/built/sanjeevni_approvals.py" "$WALK/built/packs.py" "$WALK/built/stmt_shelf.py" 2>/dev/null \
  && "$VPY" -m py_compile walk_s417.py seed_s417.py name_search_s417.py "$WALK/built/purchase_app.py" "$WALK/built/porders.py" "$WALK/built/sanjeevni_approvals.py" "$WALK/built/packs.py" "$WALK/built/stmt_shelf.py" 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in finance old old414 old412 old411 old410 old409 old408 old407 old406 old405 old404 old403 old0 old2; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
done
for side in finance old old414 old412 old411 old410 old409 old408 old407 old406 old405 old404 old403; do cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; done
[ -f "$FIN/spine/spine.db" ] && for side in finance old old414 old412 old411 old410 old409 old408 old407 old406 old405 old403; do cp -p "$FIN/spine/spine.db" "$WALK/$side/spine/"; done
for f in purchase_app.py porders.py porders.html sanjeevni_approvals.py packs.py stmt_shelf.py; do cp -p "$WALK/built/$f" "$WALK/finance/$f"; done
cp -p "$WALK/built/finance_approvals.html" "$WALK/finance/finance_ui/finance_approvals.html"
cp -p "$K411/seed_s411.py" "$K412/seed_s412.py" "$WALK/finance/"        # S411's and S412's walks import their seeds from the app copy
for side in assetapp_live assetapp_old9 assetapp_old3; do cp -p "$AST"/*.py "$AST"/*.js "$WALK/$side/" 2>/dev/null; done
cp -p "$AST/asset_register.py.bak_S409_30b26d28" "$WALK/assetapp_old9/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S409_30b26d28 missing"; rm -rf "$WALK"; exit 1; }
cp -p "$AST/asset_register.py.bak_S403_71bd3277" "$WALK/assetapp_old3/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S403_71bd3277 missing"; rm -rf "$WALK"; exit 1; }
# old414 = before S414 (S414's walk's negative control reads S410's block)
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S414_7de58315" "$WALK/old414/finance_ui/finance_approvals.html" && cp -p "$FIN/order_rules.py.bak_S414_df6196fc" "$WALK/old414/order_rules.py" \
  || { say "!! [5/10] the .bak_S414 files are missing - cannot rebuild the pre-S414 control"; rm -rf "$WALK"; exit 1; }
# old412 = before S412
for pair in "packs.py:afd429bf" "packs.html:b46d817c" "stmt_shelf.py:e74c29c0" "finance_icici.py:6d55a28a" "finance_yesbank.py:825016c0"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S412_$h" "$WALK/old412/$f" || { say "!! [5/10] $f.bak_S412_$h missing - cannot rebuild the pre-S412 control"; rm -rf "$WALK"; exit 1; }
done
# old411 = before S411
for pair in "packs.py:734c7fc0" "packs.html:03fb47f6" "finance_icici.py:a79dce49"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S411_$h" "$WALK/old411/$f" || { say "!! [5/10] $f.bak_S411_$h missing - cannot rebuild the pre-S411 control"; rm -rf "$WALK"; exit 1; }
done
# old410 = before S410
for pair in "porders.py:d08f59e2" "porders.html:76a173af" "sanjeevni_approvals.py:3cde91fb" "darpan_kal.py:401ee01c" "darpan_kal.html:1bedb469"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S410_$h" "$WALK/old410/$f" || { say "!! [5/10] $f.bak_S410_$h missing - cannot rebuild the pre-S410 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S410_77c79211" "$WALK/old410/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old410/order_rules.py"
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
# the portals: live (v29) · before S408 (v28) · before S403 (v27) · before S404 · before S400
cp -p "$POR"/*.py "$WALK/plive/"; cp -p "$POR/tile_grants.json" "$WALK/plive/"
cp -p "$POR"/*.py "$WALK/p408/"; cp -p "$POR/portal.py.bak_S408_968ca602" "$WALK/p408/portal.py"; cp -p "$POR/tile_grants.json.bak_S408_0aadfc52" "$WALK/p408/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p404/"; cp -p "$POR/portal.py.bak_S404_592ccf99" "$WALK/p404/portal.py"; cp -p "$POR/tile_grants.json.bak_S404_9231cefa" "$WALK/p404/tile_grants.json"
cp -p "$POR"/*.py "$WALK/pold/"; cp -p "$POR/portal.py.bak_S400_80d6dc44" "$WALK/pold/portal.py"; cp -p "$POR/tile_grants.json.bak_S400_7d195476" "$WALK/pold/tile_grants.json"
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do copydb "$DBF" "$WALK/scratch$i.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }; done
for i in 1 2 3; do copydb "$ADB" "$WALK/assets_scratch$i.db" || { say "!! [5/10] no scratch copy of assets.db - nothing installed"; rm -rf "$WALK"; exit 1; }; done
# S404's frozen walk answers two OPEN swap pairs of the real count 1 (answered by Darpan at 14:07-14:09 IST on 26-Sep): its scratch is a
# copy of the database backup S412's install took at 14:04:29 -- the last database that walk was green on (declared by S414, kept).
if [ -f "$S412_BAK" ]; then
  copydb "$S412_BAK" "$WALK/scratch10.db" || { say "!! [5/10] no scratch copy of $S412_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
  say "   S404's scratch copy = $(basename "$S412_BAK") (the count-1 swap pairs were still open there; declared)"
fi
# S403's and S400's frozen walks meet data the owner made AFTER S414's install ran them green at 17:45 on 26-Sep: he approved the medicine
# buying rules at 18:08 (S403 asserts 'not yet approved' and sends before the approval), tapped NEFT done for August at 19:49 (18 supplier
# messages queued -> a Needs-you line S400 asserts absent), and an orthotic family's sizes moved. Their scratch copies are therefore copies
# of the database S414's install took at 17:45:05 -- the last one those two walks were green on (declared; a diagnosis run on 27-Sep showed
# the same 7 / 1 reds on the UNPATCHED files over today's data, and 52/52 / 63/63 with this kit's files on that backup).
S414_BAK="$FIN/finance.db.bak_S414_20260926_174505"
if [ -f "$S414_BAK" ]; then
  copydb "$S414_BAK" "$WALK/scratch11.db" && copydb "$S414_BAK" "$WALK/scratch12.db" || { say "!! [5/10] no scratch copy of $S414_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
  say "   S403's and S400's scratch copies = $(basename "$S414_BAK") (before the owner's 18:08 approval and 19:49 NEFT tap; declared)"
fi
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 1800 "$VPY" -B "$KDIR/walk_s417.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S417 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s417 green on scratch copies of the live database (above)"
# S414's own walk: its --old is the box before S414 (S410's block), its --app the patched files
W414="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch14.db" timeout 900 "$VPY" -B "$K414/walk_s414.py" --app "$WALK/finance" --old "$WALK/old414" --db "$WALK/scratch14.db" 2>&1 )"
echo "$W414" | grep -E '^(WALK_S414|  FAIL|-- )' | sed 's/^/   /'
echo "$W414" | grep -q "^WALK_S414 GREEN" || { say "!! [6/10] S414's walk went red on the patched files - nothing installed"; echo "$W414" | tail -20; clean; rm -rf "$WALK"; exit 1; }
# S412's frozen walk: its scratch set back to the box as S412 found it (declared by S414, kept)
"$SPY" -c "
import sqlite3,sys; c=sqlite3.connect(sys.argv[1])
for a,d in (('9819','2026-08-10'),('9819','2026-09-10'),('9822','2026-08-14')):
    c.execute(\"INSERT OR IGNORE INTO icici_statement_period (account_ref, period_from, period_to, opening_p, closing_p, source_file, sha256, ingested_at, layout, closing_printed) VALUES (?,?,?,0,0,'prestate S417','prestate','2026-09-26T00:00:00','pipe',0)\", (a,d,d))
c.execute(\"UPDATE bank_anchor SET as_on='2026-09-10', source=\\\"ICICI Sanjeevni statement 2026-09-10..2026-09-10, the bank's own closing balance (S408 shelf)\\\", entered_by='shelf' WHERE unit='medical' AND account='icici'\")
cols=[r[1] for r in c.execute('PRAGMA table_info(stmt_file)')]
keep=[x for x in cols if x not in ('locked','unlocked_path','unlocked_at')]
if len(keep)!=len(cols):
    c.execute('CREATE TABLE stmt_file_s411 (id INTEGER PRIMARY KEY, drive_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, mtime TEXT, size INTEGER, folder TEXT NOT NULL, subfolder TEXT, slot_id INTEGER, period_from TEXT, period_to TEXT, read_status TEXT, matched_status TEXT, sha256 TEXT, fetched_at TEXT, local_path TEXT, bank TEXT, holder TEXT, tail TEXT, kind TEXT, ident_how TEXT, note TEXT, identified_at TEXT)')
    c.execute('INSERT INTO stmt_file_s411 (%s) SELECT %s FROM stmt_file' % (','.join(keep), ','.join(keep)))
    c.execute('DROP TABLE stmt_file'); c.execute('ALTER TABLE stmt_file_s411 RENAME TO stmt_file')
c.commit(); c.close()" "$WALK/scratch2.db"
ABK=""; [ -f "$S411_BAK" ] && ABK="--anchor-backup $S411_BAK"
W412="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch2.db" timeout 1500 "$VPY" -B "$K412/walk_s412.py" --app "$WALK/finance" --old "$WALK/old412" --db "$WALK/scratch2.db" $ABK 2>&1 )"
echo "$W412" | grep -E '^(WALK_S412|  FAIL|-- )' | sed 's/^/   /'
echo "$W412" | grep -q "^WALK_S412 GREEN" || { say "!! [6/10] S412's walk went red on the patched files - nothing installed"; echo "$W412" | tail -20; clean; rm -rf "$WALK"; exit 1; }
# S411's frozen walk counts the first statement of each account 'by words': its SCRATCH copy starts without the learned tails (declared)
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('UPDATE stmt_slot SET ident_tail=NULL, owner_set=NULL'); c.commit(); c.close()" "$WALK/scratch3.db"
W411="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch3.db" timeout 1500 "$VPY" -B "$K411/walk_s411.py" --app "$WALK/finance" --old "$WALK/old411" --db "$WALK/scratch3.db" 2>&1 )"
echo "$W411" | grep -E '^(WALK_S411|  FAIL|-- )' | sed 's/^/   /'
echo "$W411" | grep -q "^WALK_S411 GREEN" || { say "!! [6/10] S411's walk went red on the patched files - nothing installed"; echo "$W411" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W410="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch4.db" timeout 900 "$VPY" -B "$K410/walk_s410.py" --app "$WALK/finance" --old "$WALK/old410" --db "$WALK/scratch4.db" 2>&1 )"
echo "$W410" | grep -E '^(WALK_S410|  FAIL|-- )' | sed 's/^/   /'
echo "$W410" | grep -q "^WALK_S410 GREEN" || { say "!! [6/10] S410's walk went red on the patched files - nothing installed"; echo "$W410" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W409="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch5.db" timeout 900 "$VPY" -B "$K409/walk_s409.py" --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old9" \
         --assets-db "$WALK/assets_scratch2.db" --app "$WALK/finance" --old "$WALK/old409" --db "$WALK/scratch5.db" 2>&1 )"
echo "$W409" | grep -E '^(WALK_S409|  FAIL|-- )' | sed 's/^/   /'
echo "$W409" | grep -q "^WALK_S409 GREEN" || { say "!! [6/10] S409's walk went red on the patched files - nothing installed"; echo "$W409" | tail -20; clean; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('stmt_slot','stmt_file','pack_send','pack_tick','packs_item','packs_done','icici_statement_period','icici_statement_line','stmt_secret','stmt_secret_log','yesbank_account_statement_period','yesbank_account_statement_line')]; c.commit(); c.close()" "$WALK/scratch6.db"
W408="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch6.db" timeout 1200 "$VPY" -B "$K408/walk_s408.py" --app "$WALK/finance" --old "$WALK/old408" --db "$WALK/scratch6.db" \
         --assets-db "$WALK/assets_scratch1.db" --portal-new "$WALK/plive" --portal-old "$WALK/p408" 2>&1 )"
echo "$W408" | grep -E '^(WALK_S408|  FAIL|-- )' | sed 's/^/   /'
if echo "$W408" | grep -q "^WALK_S408 GREEN"; then :
elif echo "$W408" | grep -q "^WALK_S408 RED -- 1 of 27 failed" && [ "$(echo "$W408" | grep -c '^  FAIL')" = 1 ] && echo "$W408" | grep '^  FAIL' | grep -qF "$S408_SUPERSEDED"; then
  say "   S408's one red is the check S411 superseded ('$S408_SUPERSEDED …'): ICICI lines live in icici_statement_*, never the Yes Bank tables -- accepted, declared; 26 of 27 green"
else
  say "!! [6/10] S408's walk went red on the patched files beyond the declared supersession - nothing installed"; echo "$W408" | tail -20; clean; rm -rf "$WALK"; exit 1
fi
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('DROP TABLE IF EXISTS supplier_msg'); c.commit(); c.close()" "$WALK/scratch7.db"
W407="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch7.db" timeout 900 "$VPY" -B "$K407/walk_s407.py" --app "$WALK/finance" --old "$WALK/old407" --db "$WALK/scratch7.db" 2>&1 )"
echo "$W407" | grep -E '^(WALK_S407|  FAIL|-- )' | sed 's/^/   /'
echo "$W407" | grep -q "^WALK_S407 GREEN" || { say "!! [6/10] S407's walk went red on the patched files - nothing installed"; echo "$W407" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W406="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch8.db" timeout 900 "$VPY" -B "$K406/walk_s406.py" --app "$WALK/finance" --old "$WALK/old406" --db "$WALK/scratch8.db" 2>&1 )"
echo "$W406" | grep -E '^(WALK_S406|  FAIL|-- )' | sed 's/^/   /'
echo "$W406" | grep -q "^WALK_S406 GREEN" || { say "!! [6/10] S406's walk went red on the patched files - nothing installed"; echo "$W406" | tail -20; clean; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('purchase_neft_event','bank_sms_ignored','bank_sms_yes')]; c.commit(); c.close()" "$WALK/scratch9.db"
W405="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch9.db" timeout 900 "$VPY" -B "$K405/walk_s405.py" --app "$WALK/finance" --old "$WALK/old405" --db "$WALK/scratch9.db" 2>&1 )"
echo "$W405" | grep -E '^(WALK_S405|  FAIL|-- )' | sed 's/^/   /'
echo "$W405" | grep -q "^WALK_S405 GREEN" || { say "!! [6/10] S405's walk went red on the patched files - nothing installed"; echo "$W405" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W404="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch10.db" timeout 1500 "$VPY" -B "$K404/walk_s404.py" --app "$WALK/finance" --old "$WALK/old404" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch10.db" --portal-new "$WALK/p403" --portal-old "$WALK/p404" 2>&1 )"
echo "$W404" | grep -E '^(WALK_S404|  FAIL|-- )' | sed 's/^/   /'
echo "$W404" | grep -q "^WALK_S404 GREEN" || { say "!! [6/10] S404's walk went red on the patched files - nothing installed"; echo "$W404" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W403="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch11.db" timeout 1500 "$VPY" -B "$K403/walk_s403.py" --app "$WALK/finance" --old "$WALK/old403" \
         --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old3" --db "$WALK/scratch11.db" --assets-db "$WALK/assets_scratch3.db" \
         --portal-new "$WALK/p408" --portal-old "$WALK/p403" 2>&1 )"
echo "$W403" | grep -E '^(WALK_S403|  FAIL|-- )' | sed 's/^/   /'
echo "$W403" | grep -q "^WALK_S403 GREEN" || { say "!! [6/10] S403's walk went red on the patched files - nothing installed"; echo "$W403" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W400="$( cd "$WALK" && env $WENV NEEDS_YOU_WITHOUT_S403=1 NEEDS_YOU_WITHOUT_S406=1 NEEDS_YOU_WITHOUT_S408=1 NEEDS_YOU_WITHOUT_S410=1 FINANCE_DB="$WALK/scratch12.db" timeout 900 "$VPY" -B "$K400/walk_s400.py" --app "$WALK/finance" --old "$WALK/old0" --db "$WALK/scratch12.db" --portal-new "$WALK/p404" --portal-old "$WALK/pold" 2>&1 )"
echo "$W400" | grep -E '^(WALK_S400|  FAIL|-- )' | sed 's/^/   /'
echo "$W400" | grep -q "^WALK_S400 GREEN" || { say "!! [6/10] S400's walk went red on the patched files - nothing installed"; echo "$W400" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W402="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch13.db" timeout 900 "$VPY" -B "$K402/walk_s402.py" --app "$WALK/finance" --old "$WALK/old2" --db "$WALK/scratch13.db" 2>&1 )"
echo "$W402" | grep -E '^(WALK_S402|  FAIL|-- )' | sed 's/^/   /'
echo "$W402" | grep -q "^WALK_S402 GREEN" || { say "!! [6/10] S402's walk went red on the patched files - nothing installed"; echo "$W402" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S414's, S412's, S411's, S410's, S409's, S408's (26/27 + the declared supersession), S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files: green (above)"
copydb "$DBF" "$FIN/finance.db.bak_S417_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S417_$(m5 "${DEST[$f]}" | cut -c1-8)"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S417_$STAMP made (backup API); .bak_S417_<from8> beside all seven files"
restore() {
  say "!! RED after placing - restoring all seven files byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  systemctl restart clinic-finance || true; sleep 4
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S417_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "${DEST[$f]}" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
say "[8/10] placed; all seven md5s read back = the kit's pins"
SOUT="$( cd "$FIN" && env FINANCE_DB="$DBF" timeout 1200 "$SPY" -B "$KDIR/seed_s417.py" --app "$FIN" --db "$DBF" 2>&1 )" || { echo "$SOUT" | tail -20; restore; }
echo "$SOUT" | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /'
say "[9/10] seed_s417 on the live database (card files re-read, bank rows untouched); the JIARDIANCE name search, read-only:"
( cd /tmp && "$SPY" -B "$KDIR/name_search_s417.py" --db "$DBF" ) | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /'
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/approvals)
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/packs)
c6=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/purchase/page/orders)
say "health : finance healthz $c2 · /finance/approvals $c4 · /finance/packs $c5 · /finance/purchase/page/orders $c6 without a login (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[10/10] clinic-finance active, healthz 200, nothing 'NOT mounted'"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/purchase/page/orders · https://followup.dr-manoj.in/finance/packs · https://followup.dr-manoj.in/finance/approvals"
