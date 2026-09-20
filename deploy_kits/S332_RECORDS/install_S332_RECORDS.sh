#!/bin/bash
# =============================================================================
#  install_S332_RECORDS.sh · kit S332_RECORDS (session 273, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S332_RECORDS/install_S332_RECORDS.sh
#
#  THE OWNER, 19/20-Sep-2026 (S271_BUILD_BRIEF §2): the 360° patient record, step 1. A doctors-only page
#  https://followup.dr-manoj.in/finance/records -- patients of the day on top, one click to a patient's
#  visits, X-rays taken, blood reports (opened from the clinic's own Google Drive), Sanjeevni bills with
#  returns against the bill, procedures. Lab PDFs reach Drive through VPS_Lab_Files.gs (in this kit).
#
#  FILES:  /root/finance/records.py       NEW                          -> (TO below)
#          /root/finance/finance_app.py   41e0ffb4 (S324) -> patched ON THE BOX by patch_finance_app_s332.py
#                                         (two additive anchored edits: unit 'records' + guarded mount)
#  DATA:   business_unit 'records' + unit_role records/manoj, records/bhawna checker (seed_s332.py);
#          tables record_file, record_open, created on first use. Nothing existing is changed.
#  DOORS:  POST /finance/records/api/lab-file and GET /finance/records/api/reader, X-Finance-Cron.
# =============================================================================
set -u
KIT="S332_RECORDS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s332_walk_$STAMP"
FA_FROM=41e0ffb4ce8c94a76c251294ef3e5d31
FA_TO=3a871f53b5208edf8f218baeaa6c2882
RC_TO=b312a4d13c9eb9324cfb34abea5dc3ed
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 records.py)" = "$RC_TO" ] || { say "!! [1/8] kit records.py is not its pin - nothing installed"; exit 1; }
say "[1/8] kit gates green"
if [ "$(m5 "$FIN/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$FIN/records.py")" = "$RC_TO" ]; then
  say "-- ALREADY INSTALLED. Seed re-checked (idempotent):"; "$SPY" -B seed_s332.py "$DBF"; exit 0; fi
[ "$(m5 "$FIN/finance_app.py")" = "$FA_FROM" ] || { say "!! [2/8] finance_app.py is $(m5 "$FIN/finance_app.py"), not the S324 pin - nothing installed"; exit 1; }
[ -e "$FIN/records.py" ] && { say "!! [2/8] $FIN/records.py already exists and is not this kit's - nothing installed"; exit 1; }
say "[2/8] live pins exact"
"$SPY" -m py_compile records.py seed_s332.py patch_finance_app_s332.py walk_s332.py || { say "!! [3/8] compile failed - nothing installed"; exit 1; }
mkdir -p "$WALK/app" "$WALK/stub" || exit 1
"$SPY" -B patch_finance_app_s332.py --file "$FIN/finance_app.py" --from "$FA_FROM" --out "$WALK/finance_app.py" >/dev/null \
  && [ "$(m5 "$WALK/finance_app.py")" = "$FA_TO" ] && "$SPY" -m py_compile "$WALK/finance_app.py" \
  || { say "!! [3/8] the patch did not give $FA_TO - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green; the patch gives exactly $FA_TO"
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
[ -d "$FIN/finance_ui" ] && cp -rp "$FIN/finance_ui" "$WALK/app/"
cp -p "$WALK/finance_app.py" "$WALK/app/finance_app.py"; cp -p records.py "$WALK/app/records.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/8] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -B seed_s332.py "$WALK/walk.db" >/dev/null || { say "!! [4/8] seed on the scratch copy failed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 RECORDS_DRIVE_STUB="$WALK/stub" \
         FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$VPY" -B "$KDIR/walk_s332.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/8] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] $WOUT"
BAK="$FIN/finance_app.py.bak_S332_41e0ffb4"
\cp -p "$FIN/finance_app.py" "$BAK" || { say "!! [5/8] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$FIN/finance_app.py"; rm -f "$FIN/records.py"
  systemctl restart clinic-finance || true; sleep 3
  say "   $FIN/finance_app.py $(m5 "$FIN/finance_app.py") · records.py removed"
  exit 1
}
\cp -p records.py "$FIN/records.py" && [ "$(m5 "$FIN/records.py")" = "$RC_TO" ] || restore
\cp -p "$WALK/finance_app.py" "$FIN/finance_app.py" && [ "$(m5 "$FIN/finance_app.py")" = "$FA_TO" ] || restore
rm -rf "$WALK"
say "[5/8] placed; backup $BAK"
"$SPY" -B seed_s332.py "$DBF" || restore
say "[6/8] records unit seeded (doctors only)"
systemctl restart clinic-finance || restore
sleep 4
systemctl is-active --quiet clinic-finance || restore
say "[7/8] clinic-finance active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/records)
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/slips)
say "health : finance $c2 · /finance/records without a login $c4 · /finance/slips without a login $c5 (302 expected)"
[ "$c2" = 200 ] && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } && { [ "$c5" = 302 ] || [ "$c5" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
RD="$(cd "$FIN" && "$VPY" -B -c "import records; e=records.sa_email(); print(('reader account present (@'+e.split('@')[-1]+')') if e else 'NO READER ACCOUNT')")"
say "[8/8] all green · Drive $RD"
md5sum "$FIN/finance_app.py" "$FIN/records.py"
say "$KIT: DONE"
