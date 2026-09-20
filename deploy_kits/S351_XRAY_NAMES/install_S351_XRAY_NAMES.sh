#!/bin/bash
# =============================================================================
#  install_S351_XRAY_NAMES.sh · kit S351_XRAY_NAMES (session 277, 20-Sep-2026)
#
#  THE FINDING: the X-ray test page read 0 of 9 staff files as matched, because the staff write the clinic ID
#  at the END of the file name ("NAME 1234.jpg", a second view as "NAME 1234 ..jpg", sometimes no number on the
#  second file at all) while xray_plan() read it only at the START. Six of the nine trailing numbers were real
#  clinic IDs with X-ray slips on 19-Sep.
#
#  THE CHANGE (records.py only, the read-only test page; nothing is filed, renamed or moved):
#    - the ID is the ONE standalone run of 1-8 digits anywhere in the name (start or end);
#    - two such runs -> check folder ("which is the clinic ID?"), never a guess;
#    - a file with no number takes the ID of a same-day sister file with the same name stem, and the verdict
#      says so; no sister, or two sisters with two IDs -> check folder.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S351_XRAY_NAMES/install_S351_XRAY_NAMES.sh
#
#  FILES:  /root/finance/records.py   S346 8cdd334f -> 4c2f38b9 (full file; how it was made: make_s351.py)
#          /root/finance/finance_app.py must be 29819879 (S349) -- checked, not changed
#  WALK:   walk_s351.py on a scratch copy of finance.db, its own rows only (F-581); the LIVE records.py is the
#          negative control (it must read the same shapes as unmatched).
# =============================================================================
set -u
KIT="S351_XRAY_NAMES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s351_walk_$STAMP"
FA=29819879dec3f057b7690e004e4e87cb
RC_FROM=8cdd334f2f1329899afd8fc09df145fd
RC_TO=4c2f38b9eabca883944b32e987600963
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 records.py)" = "$RC_TO" ] || { say "!! [1/7] kit records.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
[ "$(m5 "$FIN/records.py")" = "$RC_TO" ] && { say "-- ALREADY INSTALLED (records.py $RC_TO). Nothing to do."; exit 0; }
[ "$(m5 "$FIN/records.py")" = "$RC_FROM" ] || { say "!! [2/7] records.py is $(m5 "$FIN/records.py"), not S346 - nothing installed"; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$FA" ] || { say "!! [2/7] finance_app.py is $(m5 "$FIN/finance_app.py"), not the S349 pin - nothing installed"; exit 1; }
say "[2/7] live pins exact"
mkdir -p "$WALK/app" || exit 1
cp -p records.py "$WALK/app/records.py"
"$SPY" -B -m py_compile "$WALK/app/records.py" "$KDIR/walk_s351.py" 2>/dev/null || "$VPY" -B -m py_compile "$WALK/app/records.py" "$KDIR/walk_s351.py" \
  || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/7] py_compile green"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/7] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" timeout 120 "$VPY" -B "$KDIR/walk_s351.py" "$WALK/app" "$FIN/records.py" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/7] $WOUT"
BAK="$FIN/records.py.bak_S351_8cdd334f"
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
say "[7/7] all green -- read next: https://followup.dr-manoj.in/finance/records/xray-test"
md5sum "$FIN/finance_app.py" "$FIN/records.py"
say "$KIT: DONE"
