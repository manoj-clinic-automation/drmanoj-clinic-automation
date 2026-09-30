#!/bin/bash
# =============================================================================
#  install_S439_SCANS_SMS_SCROLL.sh · kit S439_SCANS_SMS_SCROLL (session 283, 30-Sep-2026, F-660 · F-661) · Sanjeevni
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S439_SCANS_SMS_SCROLL/install_S439_SCANS_SMS_SCROLL.sh
#  (DRY=1 runs every gate, the build and every walk, then shows on scratch copies what the first pass and the replay WOULD do, and
#   places nothing. KITS=<dir> names the folder holding the S403 / S405 kits when this kit is run from a copy. NOPIN=1, with DRY=1
#   only, prints the built md5s instead of refusing on a TO mismatch.)
#
#  THREE FAULTS OF ONE MORNING (the owner, 30-Sep):
#   F-661  "reception scanned all medical bills of September, but the system is showing very few" -- the scan matcher now reads what
#          OCR writes (bill tails, the vendor by similarity, the buyer read as the vendor, a year-off date), keeps stored links, marks
#          a second scan of a bill instead of linking it, says WHY for every scan still open, and re-matches at every Marg push,
#          nightly at 23:59 (one root cron line) and once here.
#   F-660  "SMS from MacroDroid doesn't appear" -- the phone posts the SMS as the bare query string of the address; the door read only
#          a field called 'text'. It now reads any of seven field names, the raw body or the bare query, keeps the field names of a
#          refused post, and the web server's log of the earlier posts is replayed through the same door once.
#   scroll "the Days section scrolls back to the top on any Approve" -- approve() no longer redraws the whole page.
#
#  PATCHED ON THE BOX from the live bytes (make_s439.py; every anchor exactly once; FROM -> TO pins checked):
#          /root/finance/purchase_app.py                   9c40d13e -> see TO   the S439 block appended (purchase_block_s439.py); page_scans
#          /root/finance/bank_sms.py                       a70d6d96 -> see TO   read_post(), take(), the fields column, the setup line
#          /root/finance/finance_ui/finance_approvals.html 9d1eddc8 -> see TO   PARENT'S -- ONE anchored change (declared in the brief)
#  CRON:   one root line, 23:59 IST -- purchase_app.py rematch (crontab backed up first: /root/finance/crontab.bak_S439_<stamp>)
#  DATA:   after a green restart, on the live database (backed up first): the first re-match pass, and the replay of the web log's
#          earlier phone posts (once; replay_s439.py). READ ONLY: /root/assetapp/*, assets.db, the web server's access log.
#  Restarts clinic-finance ONLY. The walk (this kit's, with its negative control on the box as it is), then S403's walk and S405's
#  walk re-run on the patched files, each against its own pre-kit control.
# =============================================================================
set -u
KIT="S439_SCANS_SMS_SCROLL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
KITS="${KITS:-$KDIR/..}"
K403="$(cd "$KITS/S403_PURCHASE_ORDERS_LIVE" 2>/dev/null && pwd)"
K405="$(cd "$KITS/S405_BANK_SMS_DOOR" 2>/dev/null && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"; MRG="$ROOT/marg_ingest"; AST="$ROOT/assetapp"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPDB="$FIN/spine/spine.db"
LOGS=""; for f in ${WEBLOG:-/home/followup.dr-manoj.in/logs/followup.dr-manoj.in.access_log*}; do [ -f "$f" ] && LOGS="$LOGS --log $f"; done   # the live log and its rotated files (read only)
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s439_walk_$STAMP"
CRON_LINE='59 23 * * * cd /root/finance && FINANCE_DB=/root/finance/finance.db /root/wa/venv/bin/python3 -B /root/finance/purchase_app.py rematch >> /root/finance/scan_rematch.log 2>&1 # S439_SCANS_SMS_SCROLL'
declare -A FROM=( [purchase_app.py]=9c40d13ed222addeadf97d3f352f359a [bank_sms.py]=a70d6d96e700380d08b8e379ea0720e5
                  [finance_ui/finance_approvals.html]=9d1eddc8f96856674e1dc3638490bbeb )
declare -A TO=( [purchase_app.py]=ebe38c681f323782f0a211d1d0879b24 [bank_sms.py]=7cdd0ac9ca64921507bd0c65ab6a0e99
                [finance_ui/finance_approvals.html]=8edc44c51b46e7d7643840b485715c85 )
declare -A BUILT=( [purchase_app.py]=purchase_app.py [bank_sms.py]=bank_sms.py [finance_ui/finance_approvals.html]=finance_approvals.html )
ORDER=(purchase_app.py bank_sms.py finance_ui/finance_approvals.html)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$K403" "$K405" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in "$K403/walk_s403.py" "$K403/seed_s403.py" "$K405/walk_s405.py" "$K405/seed_s405.py"; do
  [ -f "$k" ] || { say "!! [1/10] $k must be reachable (KITS=$KITS) - the earlier walks re-run; nothing installed"; exit 1; }
done
"$VPY" -c "import pywebpush, flask, pypdf, openpyxl" 2>/dev/null || { say "!! [1/10] the venv python lacks pywebpush / flask / pypdf / openpyxl (the walks need them); nothing installed"; exit 1; }
[ -f "$ADB" ] || { say "!! [1/10] $ADB is not there - the matcher reads it; nothing installed"; exit 1; }
say "[1/10] kit gates green (SUMS, KIT_ID, the S403 / S405 walks found, the venv modules, assets.db)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the three files are at the kit's pins; cron line $(crontab -l 2>/dev/null | grep -c 'S439_SCANS_SMS_SCROLL'); clinic-finance $(systemctl is-active clinic-finance); healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"; exit 0; fi
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/10] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }; done
crontab -l 2>/dev/null | grep -q 'S439_SCANS_SMS_SCROLL' && { say "!! [2/10] a S439 cron line is already there - not this kit's; nothing installed"; exit 1; }
say "[2/10] the three live files at their FROM pins; no S439 cron line yet"
# S403's frozen walk crafts ONE scan for the first unscanned YUVIKA bill and asserts it links EXACT. Since reception's scanning of
# 29-Sep the real assets.db already holds a scan for every YUVIKA bill of September, so on a copy of TODAY's assets.db that walk picks
# another vendor's bill and goes red on the unpatched files and the patched ones alike. Its assets scratch is therefore a copy of the
# backup S435's install took on 28-Sep 10:37 (no pharmacy scan in it), beside the finance backup of 26-Sep 17:45 that S417 declared.
S414_BAK="$FIN/finance.db.bak_S414_20260926_174505"
A435_BAK="$AST/assets.db.bak_S435_20260928_103702"
for b in "$S414_BAK" "$A435_BAK"; do [ -f "$b" ] || { say "!! [2/10] $b is not there (S403's walk re-runs on it); nothing installed"; exit 1; }; done
mkdir -p "$WALK/built" "$WALK/finance/finance_ui" "$WALK/finance/spine" "$WALK/old/finance_ui" "$WALK/old/spine" "$WALK/old403/finance_ui" "$WALK/old403/spine" \
         "$WALK/old405/finance_ui" "$WALK/old405/spine" "$WALK/assetapp_live" "$WALK/assetapp_old3" "$WALK/p408" "$WALK/p403" "$WALK/uploads" "$WALK/stub" "$WALK/fig" || exit 1
"$SPY" -B make_s439.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /' || { say "!! [3/10] the build from the live bytes stopped - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ -s "$WALK/built/${BUILT[$f]}" ] || { say "!! [3/10] the build wrote no ${BUILT[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
if [ "${DRY:-0}" = 1 ] && [ "${NOPIN:-0}" = 1 ]; then
  for f in "${ORDER[@]}"; do say "   built $f $(m5 "$WALK/built/${BUILT[$f]}")"; done
else
  for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/${BUILT[$f]}")" = "${TO[$f]}" ] || { say "!! [3/10] built $f is $(m5 "$WALK/built/${BUILT[$f]}"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
  say "[3/10] live bytes + anchored edits give exactly the kit's files (three pins match)"
fi
PYS="make_s439.py walk_s439.py replay_s439.py $WALK/built/purchase_app.py $WALK/built/bank_sms.py"
( "$SPY" -m py_compile $PYS 2>/dev/null && "$VPY" -m py_compile $PYS 2>/dev/null ) \
  || { say "!! [4/10] compile on both pythons failed - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/10] compiles on /usr/bin/python3 and the venv python"
for side in finance old old403 old405; do
  cp -p "$FIN"/*.py "$WALK/$side/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
  cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null
  [ -f "$SPDB" ] && cp -p "$SPDB" "$WALK/$side/spine/"
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/${BUILT[$f]}" "$WALK/finance/$f"; done
# old403 = before S403 (S403's own negative control), as every kit since S403 rebuilt it
for pair in "purchase_app.py:9ad50878" "darpan_kal.py:1958ee7c" "darpan_kal.html:4f115f44" "sale_check.py:92ca5cb2" "sale_check.html:9c70af26" "sanjeevni_approvals.py:5fdfa364" "finance_app.py:186a500a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S403_$h" "$WALK/old403/$f" || { say "!! [5/10] $f.bak_S403_$h missing - cannot rebuild the pre-S403 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S403_6622587e" "$WALK/old403/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
rm -f "$WALK/old403/porders.py" "$WALK/old403/porders.html"
# old405 = before S405 (S405's own negative control)
for pair in "bank_sms.py:3a8f0a88" "sanjeevni_approvals.py:675aab4a"; do
  f="${pair%%:*}"; h="${pair##*:}"; cp -p "$FIN/$f.bak_S405_$h" "$WALK/old405/$f" || { say "!! [5/10] $f.bak_S405_$h missing - cannot rebuild the pre-S405 control"; rm -rf "$WALK"; exit 1; }
done
cp -p "$FIN/finance_ui/finance_approvals.html.bak_S405_c319bb56" "$WALK/old405/finance_ui/finance_approvals.html" || { rm -rf "$WALK"; exit 1; }
for side in assetapp_live assetapp_old3; do cp -p "$AST"/*.py "$AST"/*.js "$WALK/$side/" 2>/dev/null; done
cp -p "$AST/asset_register.py.bak_S403_71bd3277" "$WALK/assetapp_old3/asset_register.py" || { say "!! [5/10] asset_register.py.bak_S403_71bd3277 missing"; rm -rf "$WALK"; exit 1; }
cp -p "$POR"/*.py "$WALK/p408/"; cp -p "$POR/portal.py.bak_S408_968ca602" "$WALK/p408/portal.py"; cp -p "$POR/tile_grants.json.bak_S408_0aadfc52" "$WALK/p408/tile_grants.json"
cp -p "$POR"/*.py "$WALK/p403/"; cp -p "$POR/portal.py.bak_S403_4a5b505e" "$WALK/p403/portal.py"; cp -p "$POR/tile_grants.json.bak_S403_9e3124e0" "$WALK/p403/tile_grants.json"
cp -p "$KDIR/walk_s439.py" "$KDIR/replay_s439.py" "$WALK/"
copydb "$DBF" "$WALK/scratch1.db" || { say "!! [5/10] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$ADB" "$WALK/assets_scratch1.db" || { say "!! [5/10] no scratch copy of assets.db - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$DBF" "$WALK/scratch405.db" || { rm -rf "$WALK"; exit 1; }
copydb "$S414_BAK" "$WALK/scratch403.db" || { say "!! [5/10] no scratch copy of $S414_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$A435_BAK" "$WALK/assets_scratch403.db" || { say "!! [5/10] no scratch copy of $A435_BAK - nothing installed"; rm -rf "$WALK"; exit 1; }
[ -f "$SPDB" ] && { copydb "$SPDB" "$WALK/spine_scratch.db" || { rm -rf "$WALK"; exit 1; }; }
WENV="FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=$POR PETTY_UPLOAD_DIR=$WALK/uploads RECORDS_DRIVE_STUB=$WALK/stub MARG_ARCHIVE=$MRG/archive SPINE_DB=$WALK/spine_scratch.db"
WOUT="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch1.db" timeout 1800 "$VPY" -B "$WALK/walk_s439.py" --app "$WALK/finance" --old "$WALK/old" --db "$WALK/scratch1.db" --assets-db "$WALK/assets_scratch1.db" --kit "$WALK" 2>&1 )"
echo "$WOUT" | sed -E 's/[0-9]{10,}/##########/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S439 GREEN" || { say "!! [5/10] walk red - nothing installed"; clean; rm -rf "$WALK"; exit 1; }
clean
say "[5/10] walk_s439 green on scratch copies of finance.db and assets.db, its negative control red on the box as it is (above)"
# S405's walk asserts the OLD door keeps nothing (no ignored / Yes Bank / event table): its scratch is today's database without those three tables, as S417 ran it
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('purchase_neft_event','bank_sms_ignored','bank_sms_yes')]; c.commit(); c.close()" "$WALK/scratch405.db"
W405="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch405.db" timeout 900 "$VPY" -B "$K405/walk_s405.py" --app "$WALK/finance" --old "$WALK/old405" --db "$WALK/scratch405.db" 2>&1 )"
echo "$W405" | grep -E '^(WALK_S405|  FAIL|-- )' | sed 's/^/   /'
echo "$W405" | grep -q "^WALK_S405 GREEN" || { say "!! [6/10] S405's walk went red on the patched files - nothing installed"; echo "$W405" | tail -20; clean; rm -rf "$WALK"; exit 1; }
W403="$( cd "$WALK" && env $WENV FINANCE_DB="$WALK/scratch403.db" timeout 1500 "$VPY" -B "$K403/walk_s403.py" --app "$WALK/finance" --old "$WALK/old403" \
         --assets-new "$WALK/assetapp_live" --assets-old "$WALK/assetapp_old3" --db "$WALK/scratch403.db" --assets-db "$WALK/assets_scratch403.db" \
         --portal-new "$WALK/p408" --portal-old "$WALK/p403" 2>&1 )"
echo "$W403" | grep -E '^(WALK_S403|  FAIL|-- )' | sed 's/^/   /'
echo "$W403" | grep -q "^WALK_S403 GREEN" || { say "!! [6/10] S403's walk went red on the patched files - nothing installed"; echo "$W403" | tail -20; clean; rm -rf "$WALK"; exit 1; }
clean
say "[6/10] S405's walk (today's database without the door's three tables, as S417 ran it) and S403's walk (the finance backup of 26-Sep 17:45 and the assets backup of 28-Sep 10:37 -- declared above) re-run on the patched files, UNCHANGED, each against its own pre-kit control: green (above)"
if [ "${DRY:-0}" = 1 ]; then
  copydb "$DBF" "$WALK/fig/fin.db" && copydb "$ADB" "$WALK/fig/assets.db" && {
    ( cd "$WALK/finance" && FINANCE_DB="$WALK/fig/fin.db" ASSETS_DB="$WALK/fig/assets.db" REMATCH_WHO="dry run S439" "$VPY" -B "$WALK/finance/purchase_app.py" rematch --list 2>&1 ) | sed 's/^/   /'
    [ -n "$LOGS" ] && ( cd "$WALK/fig" && "$SPY" -B "$WALK/replay_s439.py" --app "$WALK/finance" --db "$WALK/fig/fin.db" $LOGS 2>&1 ) | sed 's/^/   /'
  }
  say "-- DRY RUN: every gate, the build and every walk green; the first pass and the replay above ran on fresh scratch copies through the built files; NOTHING placed, nothing restarted, no cron line"; clean; rm -rf "$WALK"; exit 0
fi
copydb "$DBF" "$FIN/finance.db.bak_S439_$STAMP" || { say "!! [7/10] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
crontab -l > "$FIN/crontab.bak_S439_$STAMP" 2>/dev/null || { say "!! [7/10] crontab backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="$FIN/$f.bak_S439_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [7/10] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/10] finance.db.bak_S439_$STAMP (backup API) and crontab.bak_S439_$STAMP made; .bak_S439_<from8> beside the three files"
restore() {
  say "!! RED after placing - restoring the three files byte-identically and the crontab"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  crontab "$FIN/crontab.bak_S439_$STAMP" 2>/dev/null || true
  systemctl restart clinic-finance || true; sleep 5
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   cron S439 lines: $(crontab -l 2>/dev/null | grep -c 'S439_SCANS_SMS_SCROLL') · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S439_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$WALK/built/${BUILT[$f]}" "$FIN/$f" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[8/10] placed; all three md5s read back = the kit's pins"
( crontab -l 2>/dev/null; echo "$CRON_LINE" ) | crontab - || restore
[ "$(crontab -l 2>/dev/null | grep -c 'S439_SCANS_SMS_SCROLL')" = 1 ] || restore
systemctl restart clinic-finance || restore
sleep 6
systemctl is-active --quiet clinic-finance || restore
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/purchase/page/scans)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/bank-sms)
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/approvals)
c6=$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST http://127.0.0.1:8106/finance/api/bank-sms)
say "health : finance healthz $c2 · /finance/purchase/page/scans $c3 · /finance/bank-sms $c4 · /finance/approvals $c5 without a login (302 = a login gate, expected) · the SMS door without a key $c6 (401 expected)"
[ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } && [ "$c6" = 401 ] || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[9/10] clinic-finance active, healthz 200, the pages behind their login gate, the door asks for its key, the cron line in place, nothing 'NOT mounted'"
ROUT="$( cd "$FIN" && FINANCE_DB="$DBF" REMATCH_WHO="install S439" "$VPY" -B "$FIN/purchase_app.py" rematch --list 2>&1 )" || { echo "$ROUT" | tail -20; restore; }
echo "$ROUT" | sed 's/^/   /'
echo "$ROUT" | grep -q "^S439 rematch" || restore
if [ -n "$LOGS" ]; then
  POUT="$( cd /tmp && "$SPY" -B "$KDIR/replay_s439.py" --app "$FIN" --db "$DBF" $LOGS 2>&1 )" || { echo "$POUT" | tail -20; restore; }
  echo "$POUT" | sed 's/^/   /'
else
  say "   the web server's access log was not found -- the replay did not run (the door itself is mended; the next SMS proves it)"
fi
say "[10/10] the first re-match pass ran on the live database (above; the cron takes over at 23:59); the web log's earlier phone posts replayed through the mended door (above; once)"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/approvals · https://followup.dr-manoj.in/finance/purchase/page/scans · https://followup.dr-manoj.in/finance/bank-sms"
