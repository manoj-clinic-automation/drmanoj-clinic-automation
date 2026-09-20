#!/bin/bash
# =============================================================================
#  install_S335_RECORDS_DRIVE.sh · kit S335_RECORDS_DRIVE (session 273, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S335_RECORDS_DRIVE/install_S335_RECORDS_DRIVE.sh
#
#  FOUND LIVE, 08:4x IST 20-Sep: the first blood report opened from the records page answered
#  "Drive not reachable (ModuleNotFoundError)" -- the finance web app runs under /usr/bin/python3, which has
#  no Google libraries; only the venv (/root/wa/venv) has them. This kit moves every Drive read into
#  records_drive.py, run with the venv python. Nothing else changes.
#
#  FILES:  /root/finance/records.py        S333 f284fd15 -> (TO below)
#          /root/finance/records_drive.py  NEW            -> (TO below)
#          /root/finance/finance_app.py must be 3a871f53 (S332) -- checked, not changed
#  PROOF:  after placing, the helper reads the real X-ray test folder and one real filed report from Drive.
# =============================================================================
set -u
KIT="S335_RECORDS_DRIVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s335_walk_$STAMP"
FA=3a871f53b5208edf8f218baeaa6c2882
RC_FROM=f284fd150d5b19ca949d2b88f95df9c7
RC_TO=dcb49d8cc425b52b2f79d940c2baf7fe
RD_TO=83a7171fb2e2bd8022613383641e4821
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 records.py)" = "$RC_TO" ] && [ "$(m5 records_drive.py)" = "$RD_TO" ] || { say "!! [1/7] kit files are not their pins - nothing installed"; exit 1; }
say "[1/7] kit gates green"
[ "$(m5 "$FIN/records.py")" = "$RC_TO" ] && [ "$(m5 "$FIN/records_drive.py")" = "$RD_TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
[ "$(m5 "$FIN/records.py")" = "$RC_FROM" ] || { say "!! [2/7] records.py is $(m5 "$FIN/records.py"), not S333 - nothing installed"; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$FA" ] || { say "!! [2/7] finance_app.py is not the S332 pin - nothing installed"; exit 1; }
say "[2/7] live pins exact"
"$SPY" -m py_compile records.py walk_s335.py && "$VPY" -m py_compile records_drive.py || { say "!! [3/7] compile failed - nothing installed"; exit 1; }
say "[3/7] py_compile green"
mkdir -p "$WALK/app" "$WALK/stub" || exit 1
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
[ -d "$FIN/finance_ui" ] && cp -rp "$FIN/finance_ui" "$WALK/app/"
cp -p records.py records_drive.py "$WALK/app/"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/7] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 RECORDS_DRIVE_STUB="$WALK/stub" \
         FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$VPY" -B "$KDIR/walk_s335.py" "$WALK/app" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/7] $WOUT"
BAK="$FIN/records.py.bak_S335_f284fd15"
\cp -p "$FIN/records.py" "$BAK" || { say "!! [5/7] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$FIN/records.py"; rm -f "$FIN/records_drive.py"; systemctl restart clinic-finance || true; sleep 3
  say "   $FIN/records.py $(m5 "$FIN/records.py")"; exit 1
}
\cp -p records_drive.py "$FIN/records_drive.py" && [ "$(m5 "$FIN/records_drive.py")" = "$RD_TO" ] || restore
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
XT="$("$SPY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); r=c.execute(\"SELECT value FROM record_setting WHERE key='xray_test_id'\").fetchone(); print(r[0] if r else '')" "$DBF" 2>/dev/null)"
RF="$("$SPY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); r=c.execute(\"SELECT drive_id FROM record_file WHERE drive_id<>'' ORDER BY id DESC LIMIT 1\").fetchone(); print(r[0] if r else '')" "$DBF" 2>/dev/null)"
if [ -n "$XT" ]; then N="$("$VPY" -B "$FIN/records_drive.py" list "$XT" 2>&1 | "$SPY" -c "import json,sys; print(len(json.load(sys.stdin)))" 2>&1)"; say "Drive proof : X-ray test folder read, $N file(s)"; else say "Drive proof : X-ray test folder id not set yet"; fi
if [ -n "$RF" ]; then H="$("$VPY" -B "$FIN/records_drive.py" media "$RF" 2>&1 | head -c 5)"; say "Drive proof : one filed report read, starts with ${H}"; else say "Drive proof : no filed report yet"; fi
md5sum "$FIN/finance_app.py" "$FIN/records.py" "$FIN/records_drive.py"
say "$KIT: DONE"
