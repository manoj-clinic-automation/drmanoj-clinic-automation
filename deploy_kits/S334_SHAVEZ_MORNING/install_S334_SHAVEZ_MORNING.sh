#!/bin/bash
# =============================================================================
#  install_S334_SHAVEZ_MORNING.sh · kit S334_SHAVEZ_MORNING (session 274, Sanjeevni, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S334_SHAVEZ_MORNING/install_S334_SHAVEZ_MORNING.sh
#
#  D567 items 1 and 2 (SHAVEZ_MORNING_TILE_PLAN): the 'Aaj ki reports' tile becomes Shavez's morning
#  page -- the due day, the Marg path, "aa gayi, jaanch ho rahi hai" until the spine's reader certifies
#  the file, the red banner from 10:00 when yesterday's pair is not in, the 1st-of-month rows, and the
#  owner's overdue line for his three lists inside the hub card's existing status line.
#
#  FILES:  /root/finance/reports_tile.py   78afc54b (S243) -> full-file replacement (TO below)
#  TOUCHES NOTHING ELSE: no portal.py, no tile_grants.json, no finance_app.py, no crontab, no table.
#  READS (never writes): /root/finance/spine/readings/, /root/finance/spine/spine.db, /root/marg_ingest/archive/.
# =============================================================================
set -u
KIT="S334_SHAVEZ_MORNING"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s334_walk_$STAMP"
RT_FROM=78afc54bb3c3baca75c73f9cd1dc61d6
RT_TO=2798436712be69eb3c4486a0913e38f4
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 reports_tile.py)" = "$RT_TO" ] || { say "!! [1/8] kit reports_tile.py is not its pin - nothing installed"; exit 1; }
say "[1/8] kit gates green"
if [ "$(m5 "$FIN/reports_tile.py")" = "$RT_TO" ]; then say "-- ALREADY INSTALLED ($RT_TO)"; exit 0; fi
[ "$(m5 "$FIN/reports_tile.py")" = "$RT_FROM" ] || { say "!! [2/8] reports_tile.py is $(m5 "$FIN/reports_tile.py"), not the S243 pin - nothing installed"; exit 1; }
[ -f "$FIN/spine/marg_read.py" ] || say "   note: $FIN/spine/marg_read.py absent (S331 not live?) - ticks will wait for the spine's readings"
say "[2/8] live pin exact ($RT_FROM)"
mkdir -p "$WALK/app" "$WALK/scratch" "$WALK/compile" || exit 1
# compile on COPIES: py_compile writes __pycache__ beside the source, and nothing may be written into a
# kit folder that publishes (F-538)
cp -p reports_tile.py walk_s334.py "$WALK/compile/" \
  && ( cd "$WALK/compile" && "$SPY" -m py_compile reports_tile.py walk_s334.py && "$VPY" -m py_compile reports_tile.py walk_s334.py ) \
  || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green on both pythons (on copies; the kit folder stays clean)"
( cd "$WALK/app" && cp -p "$KDIR/reports_tile.py" . && "$VPY" -B reports_tile.py 2>&1 | tail -1 | tee "$WALK/selftest.txt" )
grep -q " 0 failures" "$WALK/selftest.txt" || { say "!! [4/8] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] selftest: $(cat "$WALK/selftest.txt")"
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$KDIR/reports_tile.py" "$WALK/app/reports_tile.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [5/8] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && timeout 170 "$VPY" -B "$KDIR/walk_s334.py" "$WALK/app" "$WALK/walk.db" "$WALK/scratch" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK OK" || { say "!! [5/8] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/8] walk green on a scratch copy of the live database, the real readings and the real kept files (read-only)"
BAK="$FIN/reports_tile.py.bak_S334_${RT_FROM:0:8}"
\cp -p "$FIN/reports_tile.py" "$BAK" || { say "!! [6/8] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$FIN/reports_tile.py"
  systemctl restart clinic-finance || true; sleep 3
  say "   $FIN/reports_tile.py $(m5 "$FIN/reports_tile.py")"
  exit 1
}
\cp -p reports_tile.py "$FIN/reports_tile.py" && [ "$(m5 "$FIN/reports_tile.py")" = "$RT_TO" ] || restore
rm -rf "$WALK"
say "[6/8] placed $RT_TO; backup $BAK"
systemctl restart clinic-finance || restore
sleep 4
systemctl is-active --quiet clinic-finance || restore
say "[7/8] clinic-finance active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/reports/aaj)
c4=$(curl -s -m 8 http://127.0.0.1:8106/finance/reports/aaj/api/healthz)
say "health : finance $c2 · /finance/reports/aaj without a login $c3 (302/401 = the login gate, expected) · $c4"
[ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } && echo "$c4" | grep -q "$KIT" || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "reports_tile NOT mounted" && restore
LINE="$( cd "$FIN" && SPINE_DIR="$FIN/spine" "$VPY" -B -c "
import sqlite3, reports_tile as rt
cx = sqlite3.connect('file:%s?mode=ro' % '$DBF', uri=True); cx.row_factory = sqlite3.Row
s = rt.status(cx); print(s['line']); print('   rows: ' + ' | '.join('%s=%s' % (r['key'], r['state']) for r in s['rows']))
" 2>&1 | tail -2 )"
say "[8/8] the page now reads: $LINE"
md5sum "$FIN/reports_tile.py"
say "$KIT: DONE -- open https://followup.dr-manoj.in/finance/reports/aaj"
