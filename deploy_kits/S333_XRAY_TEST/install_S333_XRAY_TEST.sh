#!/bin/bash
# =============================================================================
#  install_S333_XRAY_TEST.sh · kit S333_XRAY_TEST (session 273, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S333_XRAY_TEST/install_S333_XRAY_TEST.sh
#
#  THE OWNER (S271_BUILD_BRIEF §2.7 step 2): the X-ray inbox, READ-ONLY TEST RUN FIRST. Staff put the pen
#  drive's X-ray files into Google Drive -> Clinic Records -> X-ray test. The doctors' page
#  https://followup.dr-manoj.in/finance/records/xray-test shows each file: original name -> proposed name
#  -> matched or not, and whether the X-ray PC's clock agrees with the slip. NOTHING is renamed or moved.
#
#  FILES:  /root/finance/records.py   S332 b312a4d1 -> (TO below)
#          /root/finance/finance_app.py must be 3a871f53 (S332) -- checked, not changed
#  DATA:   table record_setting (the folder ids), created on first use.
#  DOOR:   POST /finance/records/api/folders, X-Finance-Cron.
# =============================================================================
set -u
KIT="S333_XRAY_TEST"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s333_walk_$STAMP"
FA=3a871f53b5208edf8f218baeaa6c2882
RC_FROM=b312a4d13c9eb9324cfb34abea5dc3ed
RC_TO=f284fd150d5b19ca949d2b88f95df9c7
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 records.py)" = "$RC_TO" ] || { say "!! [1/7] kit records.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
[ "$(m5 "$FIN/records.py")" = "$RC_TO" ] && { say "-- ALREADY INSTALLED (records.py $RC_TO). Nothing to do."; exit 0; }
[ "$(m5 "$FIN/records.py")" = "$RC_FROM" ] || { say "!! [2/7] records.py is $(m5 "$FIN/records.py"), not S332 - nothing installed"; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$FA" ] || { say "!! [2/7] finance_app.py is not the S332 pin - nothing installed"; exit 1; }
say "[2/7] live pins exact"
"$SPY" -m py_compile records.py walk_s333.py || { say "!! [3/7] compile failed - nothing installed"; exit 1; }
say "[3/7] py_compile green"
mkdir -p "$WALK/app" "$WALK/stub" || exit 1
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
[ -d "$FIN/finance_ui" ] && cp -rp "$FIN/finance_ui" "$WALK/app/"
cp -p records.py "$WALK/app/records.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/7] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 RECORDS_DRIVE_STUB="$WALK/stub" \
         FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$VPY" -B "$KDIR/walk_s333.py" "$WALK/app" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/7] $WOUT"
BAK="$FIN/records.py.bak_S333_b312a4d1"
\cp -p "$FIN/records.py" "$BAK" || { say "!! [5/7] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$FIN/records.py"; systemctl restart clinic-finance || true; sleep 3
  say "   $FIN/records.py $(m5 "$FIN/records.py")"; exit 1
}
\cp -p records.py "$FIN/records.py" && [ "$(m5 "$FIN/records.py")" = "$RC_TO" ] || restore
say "[5/7] placed; backup $BAK"
systemctl restart clinic-finance || restore
sleep 4
systemctl is-active --quiet clinic-finance || restore
say "[6/7] clinic-finance active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/records/xray-test)
say "health : finance $c2 · /finance/records/xray-test without a login $c4 (302 expected)"
[ "$c2" = 200 ] && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[7/7] all green"
md5sum "$FIN/finance_app.py" "$FIN/records.py"
say "$KIT: DONE"
