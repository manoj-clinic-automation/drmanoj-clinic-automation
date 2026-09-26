#!/bin/bash
# =============================================================================
#  install_S412_YESBANK_UNLOCK.sh · kit S412_YESBANK_UNLOCK (session 283, 26-Sep-2026) · OWNER: PARENT (clinic), follow-up to S408/S411
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S412_YESBANK_UNLOCK/install_S412_YESBANK_UNLOCK.sh
#
#  THE SHELF OPENS YES BANK'S PASSWORD-LOCKED E-STATEMENTS ITSELF. The owner types the bank's statement password once on the Month-end
#  packs page ('Statement passwords'); it lives in finance.db only (stmt_secret), is never printed, logged or sent back to a page. Every
#  night (and on every re-read) the venv python opens the locked PDFs the candidates fit (pypdf; AES-256 and RC4 alike -- the two ciphers
#  the five real files use), keeps the locked original and reads the opened copy like any other statement. The branch's own statements
#  stay the first source: a locked copy of a month the branch already sent is 'duplicate of branch copy'. The four non-Sanjeevni Yes Bank
#  accounts go to their own tables (yesbank_account_statement_*), never the shared ones the owner's Bank card reads. The ICICI anchor moves
#  only on a statement with a real header period and a printed closing (restored to 31-Aug at install: S411's run had moved it to 10-Sep on
#  a text statement's degenerate header); the pipe .txt's period is widened to its rows.
#
#  PATCHED ON THE BOX from the live bytes (make_s412.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/packs.py             afd429bf -> 359403f7   the unlock step, stmt_secret + the owner-only API, the duplicate rule,
#                                                                    the per-account Yes Bank tables, the anchor rule, the Needs-you line
#          /root/finance/packs.html           b46d817c -> 2e06943b   the 'Statement passwords' card; 'opened' / 'no password' words
#          /root/finance/stmt_shelf.py        e74c29c0 -> 94f456ce   the 'unlock' command (venv, pypdf) -- counts only
#          /root/finance/finance_icici.py     6d55a28a -> 7ace56b7   (3b) the degenerate pipe period widened to the rows; VERSION stays 1.1
#          /root/finance/finance_yesbank.py   825016c0 -> 5a088cd9   ingest_statement(..., tables=None) -- anchored, declared (the reader itself untouched)
#  NOT touched: sanjeevni_approvals.py / finance_approvals.html -- the Needs-you line rides the packs hook S408 wired (declared in the README).
#  INSTALLED INTO THE VENV, STATED HERE: pypdf==4.3.1 (pure python; /root/wa/venv only, the service python is untouched) when it is missing.
#  Restarts clinic-finance ONLY. finance.db backed up first. The seed restores the anchor, widens the four pipe periods, flags the five locked
#  files; then the 05:40 fetcher runs once by hand. The walk (this kit's), then S411's, S410's, S409's, S408's (26/27 + the declared
#  supersession), S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files.
# =============================================================================
set -u
KIT="S412_YESBANK_UNLOCK"
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
GAS="$KDIR/../GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s412_walk_$STAMP"
S408_SUPERSEDED="the ICICI reader read the fixture into bank_statement_period/_line"
S411_BAK="$FIN/finance.db.bak_S411_20260926_124432"
declare -A FROM=( [packs.py]=afd429bf8c0e7f685adda7d688045ab7 [packs.html]=b46d817c7a77944c4280ac72f95a6808 [stmt_shelf.py]=e74c29c0a5bb41f21cd2f7c1c8d3ad5d
                  [finance_icici.py]=6d55a28aac170b1ab5899faa60eaa257 [finance_yesbank.py]=825016c02364dc5d22027ff192d1d29d )
declare -A TO=( [packs.py]=359403f792eaafad37d4eeac3f762641 [packs.html]=2e06943b991063dad3b23c74858533d4 [stmt_shelf.py]=94f456ce0a6f469ecd7d3f16ca1e874e
                [finance_icici.py]=7ace56b77cd87d29352acb2d0f6cbe48 [finance_yesbank.py]=5a088cd91bc1b8d873cc779f3fa9b0a8 )
declare -A DEST=( [packs.py]="$FIN/packs.py" [packs.html]="$FIN/packs.html" [stmt_shelf.py]="$FIN/stmt_shelf.py" [finance_icici.py]="$FIN/finance_icici.py" [finance_yesbank.py]="$FIN/finance_yesbank.py" )
ORDER=(packs.py packs.html stmt_shelf.py finance_icici.py finance_yesbank.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K400" "$K402" "$K403" "$K404" "$K405" "$K406" "$K407" "$K408" "$K409" "$K410" "$K411" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K400/walk_s400.py" "$K400/seed_s400.py" "$K402/walk_s402.py" "$K403/walk_s403.py" "$K403/seed_s403.py" "$K404/walk_s404.py" "$K404/seed_s404.py" "$K405/walk_s405.py" "$K405/seed_s405.py" "$K406/walk_s406.py" "$K406/seed_s406.py" "$K407/walk_s407.py" "$K407/seed_s407.py" "$K408/walk_s408.py" "$K408/seed_s408.py" "$K409/walk_s409.py" "$K409/seed_s409.py" "$K410/walk_s410.py" "$K410/seed_s410.py" "$K411/walk_s411.py" "$K411/seed_s411.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must sit beside this kit (the earlier walks re-run) - nothing installed"; exit 1; }
done
[ -f "$GAS" ] || { say "!! [1/10] the filer script $GAS is not beside this kit (S408's walk reads it) - nothing installed"; exit 1; }
for t in pdftotext pdfunite pdfinfo convert pdftoppm; do command -v "$t" >/dev/null 2>&1 || { say "!! [1/10] $t is not on the box; nothing installed"; exit 1; }; done
[ -x "$VPY" ] || { say "!! [1/10] the venv python $VPY is not there - nothing installed"; exit 1; }
if ! "$VPY" -c "import pypdf" 2>/dev/null; then
  say "   installing pypdf==4.3.1 into the venv ($VPY) -- the ONE thing this kit installs, and only there (the service python is untouched)"
  "$VPY" -m pip install -q "pypdf==4.3.1" 2>&1 | grep -v -e "pip version" -e "consider upgrading" | sed 's/^/   /'
  "$VPY" -c "import pypdf" 2>/dev/null || { say "!! [1/10] pypdf could not be installed into the venv - nothing installed"; exit 1; }
fi
"$VPY" -c "import pypdf, cryptography; from pypdf._crypt_providers import crypt_provider; assert crypt_provider[0]=='cryptography', crypt_provider; print('   venv: pypdf', pypdf.__version__, '· AES through', crypt_provider)" \
  || { say "!! [1/10] pypdf is in the venv but its AES provider is not the venv's cryptography - nothing installed"; exit 1; }
say "[1/10] kit gates green (S400-S411 walks found; the filer script; the PDF/image tools; pypdf in the venv)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED. Shelf re-checked:"; cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B "$FIN/stmt_shelf.py" status 2>/dev/null | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | awk -F'|' '{print $1"|"$4"|"$5"|"$6"|"$7"|"$8}' | sort | uniq -c | sort -rn | head -12; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/10] ${DEST[$f]} is $(m5 "${DEST[$f]}"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
say "[2/10] every live file at its FROM pin"
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" "$WALK/old411/finance_ui" "$WALK/old411/spine" "$WALK/old410/finance_ui" "$WALK/old410/spine" "$WALK/old409/finance_ui" "$WALK/old409/spine" "$WALK/old408/finance_ui" "$WALK/old408/spine" \
         "$WALK/old407/finance_ui" "$WALK/old407/spine" "$WALK/old406/finance_ui" "$WALK/old406/spine" "$WALK/old405/finance_ui" "$WALK/old405/spine" "$WALK/old404/finance_ui" "$WALK/old404/spine" \
         "$WALK/old403/finance_ui" "$WALK/old403/spine" "$WALK/old0/finance_ui" "$WALK/old2/finance_ui" "$WALK/marg_ingest" "$WALK/marg_old" "$WALK/assetapp_live" "$WALK/assetapp_old9" "$WALK/assetapp_old3" \
         "$WALK/plive" "$WALK/p408" "$WALK/p403" "$WALK/p404" "$WALK/pold" "$WALK/uploads" "$WALK/stub" || exit 1
"$SPY" -B make_s412.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/10] live bytes + anchored edits give exactly the kit's five files (pins match)"
( "$SPY" -m py_compile seed_s412.py make_s412.py walk_s412.py "$WALK/built/packs.py" "$WALK/built/stmt_shelf.py" "$WALK/built/finance_icici.py" "$WALK/built/finance_yesbank.py" 2>/dev/null \
  && "$VPY" -m py_compile seed_s412.py walk_s412.py "$WALK/built/packs.py" "$WALK/built/stmt_shelf.py" "$WALK/built/finance_icici.py" "$WALK/built/finance_yesbank.py" 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in finance old old411 old410 old409 old408 old407 old406 old405 old404 old403 old0 old2; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
done
for side in finance old old411 old410 old409 old408 old407 old406 old405 old404 old403; do cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; done
[ -f "$FIN/spine/spine.db" ] && for side in finance old old411 old410 old409 old408 old407 old406 old405 old403; do cp -p "$FIN/spine/spine.db" "$WALK/$side/spine/"; done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/finance/$f"; done
cp -p seed_s412.py "$WALK/finance/"
cp -p "$K411/seed_s411.py" "$WALK/finance/"        # S411's walk imports its seed from the app copy (as S411's installer placed it)
for side in assetapp_live assetapp_old9 assetapp_old3; do cp -p "$AST"/*.py "$AST"/*.js "$WALK/$side/" 2>/dev/null; done
cp -p "$AST/asset_register.py.bak_S409_30b26d28" "$WALK/assetapp_old9/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S409_30b26d28 missing"; rm -rf "$WALK"; exit 1; }
cp -p "$AST/asset_register.py.bak_S403_71bd3277" "$WALK/assetapp_old3/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S403_71bd3277 missing"; rm -rf "$WALK"; exit 1; }
# old411 = before S411 (S411's own walk needs its pre-state as the control)
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
# the portals: live (v29) · before S408 (v28 = what S403/S404 left) · before S403 (v27) · before S404 · before S400
cp -p "$POR"/*.py "$WALK/plive/"; cp -p "$POR/tile_grants.json" "$WALK/plive/"
cp -p "$POR"/*.py "$WALK/p408/"; cp -p "$POR/portal.py.bak_S408_968ca602" "$WALK/p408/portal.py"; cp -p "$POR/tile_grants.json.bak_S408_0aadfc52" "$WALK/p408/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p404/"; cp -p "$POR/portal.py.bak_S404_592ccf99" "$WALK/p404/portal.py"; cp -p "$POR/tile_grants.json.bak_S404_9231cefa" "$WALK/p404/tile_grants.json"
cp -p "$POR"/*.py "$WALK/pold/"; cp -p "$POR/portal.py.bak_S400_80d6dc44" "$WALK/pold/portal.py"; cp -p "$POR/tile_grants.json.bak_S400_7d195476" "$WALK/pold/tile_grants.json"
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do copydb "$DBF" "$WALK/scratch$i.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }; done
for i in 1 2 3; do copydb "$ADB" "$WALK/assets_scratch$i.db" || { say "!! [5/10] no scratch copy of assets.db - nothing installed"; rm -rf "$WALK"; exit 1; }; done
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive"
ABK=""; [ -f "$S411_BAK" ] && ABK="--anchor-backup $S411_BAK"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 1500 "$VPY" -B "$KDIR/walk_s412.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" $ABK 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S412 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s412 green on scratch copies of the live database (above)"
# S411's frozen walk re-identifies the REAL files in its own scratch copy and counts the first statement of each account 'by words'; the live
# shelf has carried the learned tails since S411's own seed (26-Sep 12:44 IST), so its SCRATCH copy starts as S411 found the box: no learned tail.
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('UPDATE stmt_slot SET ident_tail=NULL, owner_set=NULL'); c.commit(); c.close()" "$WALK/scratch12.db"
W411="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch12.db" timeout 1500 "$VPY" -B "$K411/walk_s411.py" --app "$WALK/finance" --old "$WALK/old411" --db "$WALK/scratch12.db" 2>&1 )"
echo "$W411" | grep -E '^(WALK_S411|  FAIL|-- )' | sed 's/^/   /'
echo "$W411" | grep -q "^WALK_S411 GREEN" || { say "!! [6/10] S411's walk went red on the patched files - nothing installed"; echo "$W411" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W410="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch2.db" timeout 900 "$VPY" -B "$K410/walk_s410.py" --app "$WALK/finance" --old "$WALK/old410" --db "$WALK/scratch2.db" 2>&1 )"
echo "$W410" | grep -E '^(WALK_S410|  FAIL|-- )' | sed 's/^/   /'
echo "$W410" | grep -q "^WALK_S410 GREEN" || { say "!! [6/10] S410's walk went red on the patched files - nothing installed"; echo "$W410" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W409="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch3.db" timeout 900 "$VPY" -B "$K409/walk_s409.py" --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old9" \
         --assets-db "$WALK/assets_scratch2.db" --app "$WALK/finance" --old "$WALK/old409" --db "$WALK/scratch3.db" 2>&1 )"
echo "$W409" | grep -E '^(WALK_S409|  FAIL|-- )' | sed 's/^/   /'
echo "$W409" | grep -q "^WALK_S409 GREEN" || { say "!! [6/10] S409's walk went red on the patched files - nothing installed"; echo "$W409" | tail -20; clean; rm -rf "$WALK"; exit 1; }
# S408's frozen walk: the shelf tables it seeds itself are dropped from its SCRATCH copy; ONE check is superseded since S411 (declared) -- every other check must be green.
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('stmt_slot','stmt_file','pack_send','pack_tick','packs_item','packs_done','icici_statement_period','icici_statement_line','stmt_secret','stmt_secret_log','yesbank_account_statement_period','yesbank_account_statement_line')]; c.commit(); c.close()" "$WALK/scratch4.db"
W408="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch4.db" timeout 1200 "$VPY" -B "$K408/walk_s408.py" --app "$WALK/finance" --old "$WALK/old408" --db "$WALK/scratch4.db" \
         --assets-db "$WALK/assets_scratch1.db" --portal-new "$WALK/plive" --portal-old "$WALK/p408" 2>&1 )"
echo "$W408" | grep -E '^(WALK_S408|  FAIL|-- )' | sed 's/^/   /'
if echo "$W408" | grep -q "^WALK_S408 GREEN"; then :
elif echo "$W408" | grep -q "^WALK_S408 RED -- 1 of 27 failed" && [ "$(echo "$W408" | grep -c '^  FAIL')" = 1 ] && echo "$W408" | grep '^  FAIL' | grep -qF "$S408_SUPERSEDED"; then
  say "   S408's one red is the check S411 superseded ('$S408_SUPERSEDED …'): ICICI lines live in icici_statement_*, never the Yes Bank tables -- accepted, declared; 26 of 27 green"
else
  say "!! [6/10] S408's walk went red on the patched files beyond the declared supersession - nothing installed"; echo "$W408" | tail -20; clean; rm -rf "$WALK"; exit 1
fi
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('DROP TABLE IF EXISTS supplier_msg'); c.commit(); c.close()" "$WALK/scratch5.db"
W407="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch5.db" timeout 900 "$VPY" -B "$K407/walk_s407.py" --app "$WALK/finance" --old "$WALK/old407" --db "$WALK/scratch5.db" 2>&1 )"
echo "$W407" | grep -E '^(WALK_S407|  FAIL|-- )' | sed 's/^/   /'
echo "$W407" | grep -q "^WALK_S407 GREEN" || { say "!! [6/10] S407's walk went red on the patched files - nothing installed"; echo "$W407" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W406="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch6.db" timeout 900 "$VPY" -B "$K406/walk_s406.py" --app "$WALK/finance" --old "$WALK/old406" --db "$WALK/scratch6.db" 2>&1 )"
echo "$W406" | grep -E '^(WALK_S406|  FAIL|-- )' | sed 's/^/   /'
echo "$W406" | grep -q "^WALK_S406 GREEN" || { say "!! [6/10] S406's walk went red on the patched files - nothing installed"; echo "$W406" | tail -20; clean; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('purchase_neft_event','bank_sms_ignored','bank_sms_yes')]; c.commit(); c.close()" "$WALK/scratch7.db"
W405="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch7.db" timeout 900 "$VPY" -B "$K405/walk_s405.py" --app "$WALK/finance" --old "$WALK/old405" --db "$WALK/scratch7.db" 2>&1 )"
echo "$W405" | grep -E '^(WALK_S405|  FAIL|-- )' | sed 's/^/   /'
echo "$W405" | grep -q "^WALK_S405 GREEN" || { say "!! [6/10] S405's walk went red on the patched files - nothing installed"; echo "$W405" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W404="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch8.db" timeout 1500 "$VPY" -B "$K404/walk_s404.py" --app "$WALK/finance" --old "$WALK/old404" --marg-new "$WALK/marg_ingest" --marg-old "$WALK/marg_old" \
         --db "$WALK/scratch8.db" --portal-new "$WALK/p403" --portal-old "$WALK/p404" 2>&1 )"
echo "$W404" | grep -E '^(WALK_S404|  FAIL|-- )' | sed 's/^/   /'
echo "$W404" | grep -q "^WALK_S404 GREEN" || { say "!! [6/10] S404's walk went red on the patched files - nothing installed"; echo "$W404" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W403="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch9.db" timeout 1500 "$VPY" -B "$K403/walk_s403.py" --app "$WALK/finance" --old "$WALK/old403" \
         --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old3" --db "$WALK/scratch9.db" --assets-db "$WALK/assets_scratch3.db" \
         --portal-new "$WALK/p408" --portal-old "$WALK/p403" 2>&1 )"
echo "$W403" | grep -E '^(WALK_S403|  FAIL|-- )' | sed 's/^/   /'
echo "$W403" | grep -q "^WALK_S403 GREEN" || { say "!! [6/10] S403's walk went red on the patched files - nothing installed"; echo "$W403" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W400="$( cd "$WALK" && env $WENV NEEDS_YOU_WITHOUT_S403=1 NEEDS_YOU_WITHOUT_S406=1 NEEDS_YOU_WITHOUT_S408=1 NEEDS_YOU_WITHOUT_S410=1 FINANCE_DB="$WALK/scratch10.db" timeout 900 "$VPY" -B "$K400/walk_s400.py" --app "$WALK/finance" --old "$WALK/old0" --db "$WALK/scratch10.db" --portal-new "$WALK/p404" --portal-old "$WALK/pold" 2>&1 )"
echo "$W400" | grep -E '^(WALK_S400|  FAIL|-- )' | sed 's/^/   /'
echo "$W400" | grep -q "^WALK_S400 GREEN" || { say "!! [6/10] S400's walk went red on the patched files - nothing installed"; echo "$W400" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W402="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch11.db" timeout 900 "$VPY" -B "$K402/walk_s402.py" --app "$WALK/finance" --old "$WALK/old2" --db "$WALK/scratch11.db" 2>&1 )"
echo "$W402" | grep -E '^(WALK_S402|  FAIL|-- )' | sed 's/^/   /'
echo "$W402" | grep -q "^WALK_S402 GREEN" || { say "!! [6/10] S402's walk went red on the patched files - nothing installed"; echo "$W402" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S411's, S410's, S409's, S408's (26/27 + the declared supersession), S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run on the patched files: green (above)"
copydb "$DBF" "$FIN/finance.db.bak_S412_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S412_$(m5 "${DEST[$f]}" | cut -c1-8)"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S412_$STAMP made; .bak_S412_<from8> beside each of the five files"
restore() {
  say "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  systemctl restart clinic-finance || true; sleep 4
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S412_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/$f" "${DEST[$f]}" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
say "[8/10] placed; every md5 read back = the kit's pin"
FINANCE_DIR="$FIN" "$SPY" -B seed_s412.py "$DBF" | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /' || restore
say "[9/10] the anchor, the pipe periods, the locked files seeded (above); no password stored -- the owner types it on the page"
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/packs)
say "health : finance healthz $c2 · /finance/packs without a login $c4 (302 = a login gate, expected)"
[ "$c2" = 200 ] && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "-- the 05:40 fetcher, once by hand (new files fetched, identified; nothing unlocks until the password is typed):"
( cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B "$FIN/stmt_shelf.py" run 2>/dev/null | grep -v Warning | sed -E 's/[0-9]{6,}([0-9]{4})/XXXX\1/g' | sed 's/^/   /' ) || say "   (the fetcher returned non-zero -- read its output above)"
cd "$KDIR"
say "[10/10] clinic-finance active, healthz 200, nothing 'NOT mounted'"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/packs"
