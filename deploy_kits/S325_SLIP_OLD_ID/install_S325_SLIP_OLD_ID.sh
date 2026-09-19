#!/bin/bash
# =============================================================================
#  install_S325_SLIP_OLD_ID.sh · kit S325_SLIP_OLD_ID (session 271, 19-Sep-2026, the first live morning)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S325_SLIP_OLD_ID/install_S325_SLIP_OLD_ID.sh
#
#  THE OWNER: "2681 CLINIC ID FLAGGED AS NAYA". The patient master (patient_ref) has no row for some
#  old IDs, and S324 read "no row" as "new". His rule is "the system knows till which number the clinic
#  ID exists": NEW means ABOVE the highest known ID. An ID at or below it is an old patient; the name is
#  taken from Docterz's own day lines when the master lacks it, else from the night's export.
#
#  FILES:  /root/finance/slip_log.py  f4dc7110 -> 121174ae  (full-file replacement, backed up beside itself)
#          /root/finance/finance_app.py must be 41e0ffb4 (S324) -- checked, not changed
#  DATA:   fix_s325.py -- today's slips at or below the highest known ID lose the NEW mark. slip table only.
#  Gates: SUMS + KIT_ID -> pins -> compile -> THE WALK ON THIS BOX (81 checks, scratch copy) -> backup ->
#  place -> fix -> restart clinic-finance -> health. Any red after placing: the file restored, restarted.
# =============================================================================
set -u
KIT="S325_SLIP_OLD_ID"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s325_walk_$STAMP"
FROM=f4dc7110a19258dea6a7473bfbb994a9
TO=121174aeb311c6bd8255f9d34998dbb2
FA=41e0ffb4ce8c94a76c251294ef3e5d31
DEST="$FIN/slip_log.py"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 slip_log.py)" = "$TO" ] || { say "!! [1/7] kit slip_log.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$DEST")" = "$TO" ]; then say "-- ALREADY INSTALLED. Re-running the fix (idempotent):"; "$SPY" -B fix_s325.py "$DBF"; exit 0; fi
[ "$(m5 "$DEST")" = "$FROM" ] || { say "!! [2/7] $DEST is $(m5 "$DEST"), expected $FROM - nothing installed"; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$FA" ] || { say "!! [2/7] finance_app.py is not the S324 pin - nothing installed"; exit 1; }
say "[2/7] live pins exact"
"$SPY" -m py_compile slip_log.py fix_s325.py || { say "!! [3/7] compile failed - nothing installed"; exit 1; }
say "[3/7] py_compile green"
mkdir -p "$WALK/app" || exit 1
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
[ -d "$FIN/finance_ui" ] && cp -rp "$FIN/finance_ui" "$WALK/app/"
cp -p slip_log.py "$WALK/app/slip_log.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/7] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); [c.execute('DROP TABLE IF EXISTS '+t) for t in ('slip_item','slip','slip_book')]; c.commit()" "$WALK/walk.db"
"$SPY" -B seed_s324.py "$WALK/walk.db" >/dev/null || { say "!! [4/7] seed on the scratch copy failed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 SLIP_NOW="$(date +%Y-%m-%dT%H:%M:%S)" \
         FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$SPY" -B "$KDIR/walk_s325.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] $WOUT"
BAK="$DEST.bak_S325_${FROM:0:8}"
\cp -p "$DEST" "$BAK" || { say "!! [5/7] backup failed - nothing placed"; exit 1; }
restore() { say "!! RED - restoring slip_log.py"; \cp -p "$BAK" "$DEST"; systemctl restart clinic-finance; sleep 3; say "   $DEST $(m5 "$DEST")"; exit 1; }
\cp -p slip_log.py "$DEST" || restore
[ "$(m5 "$DEST")" = "$TO" ] || restore
say "[5/7] placed (backup $BAK)"
"$SPY" -B fix_s325.py "$DBF" || restore
systemctl restart clinic-finance || restore
sleep 4
systemctl is-active --quiet clinic-finance || restore
say "[6/7] fixed; clinic-finance active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/slips)
say "health : finance $c2 · /finance/slips without a login $c4 (302 expected)"
[ "$c2" = 200 ] && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[7/7] all green"
md5sum "$DEST"
say "$KIT: DONE"
