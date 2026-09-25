#!/bin/bash
# =============================================================================
#  install_S399_DAY_TRUTH_5.sh · kit S399_DAY_TRUTH_5 (session 283, Sanjeevni, 25-Sep-2026)
#  F-632: a procedure / home-medicine bill that the ingest attached to a patient (the lookup ladder,
#  or a clinic ID whose name disagreed) was never taken off the day's cash -- A003806 of 23-Sep,
#  PROSIJER, Rs 195. day_resync now reads Darpan's label words in the bill text the ingest keeps for
#  those bills too; an approved day holding such a bill is named, never touched.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S399_DAY_TRUTH_5/install_S399_DAY_TRUTH_5.sh
#
#    /root/finance/day_resync.py  ddbb12eb (S367) -> c62e98b9 (S399)   -- the same cron line runs it
#    finance.db: backed up first; the first run adds A003806 (23-Sep, 195) as procedure medicine
#    NOTHING restarted (cron-only file). No parent file is touched.
# =============================================================================
set -u
KIT="S399_DAY_TRUTH_5"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s399_walk_$STAMP"
FROM=ddbb12eb7835b29d44804105432e19a7
TO=c62e98b971fab7c6802b74b9029c291e
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 day_resync.py)" = "$TO" ] || { say "!! [1/6] kit day_resync.py is not its pin - nothing installed"; exit 1; }
say "[1/6] kit gates green"
if [ "$(m5 "$FIN/day_resync.py")" = "$TO" ]; then
  say "-- ALREADY INSTALLED; a dry run:"; ( cd "$FIN" && "$VPY" -B day_resync.py --dry-run --no-reconcile 2>&1 | sed -n '/HOME\/PROC/,$p' | sed 's/^/   /' ); exit 0; fi
[ "$(m5 "$FIN/day_resync.py")" = "$FROM" ] || { say "!! [2/6] $FIN/day_resync.py is not its pin ${FROM:0:8} - nothing installed"; exit 1; }
say "[2/6] live file at its pin (S367 ${FROM:0:8})"
mkdir -p "$WALK" || exit 1
cp -p day_resync.py walk_s399.py "$WALK/" && cp -p "$FIN/day_resync.py" "$WALK/day_resync_S367.py" || exit 1
( cd "$WALK" && "$SPY" -m py_compile day_resync.py && "$VPY" -m py_compile day_resync.py ) || { say "!! [3/6] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/6] compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/6] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK" && FINANCE_DB="$WALK/scratch.db" timeout 300 "$VPY" -B walk_s399.py --db "$WALK/scratch.db" --new day_resync.py --old day_resync_S367.py 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S399 GREEN" || { say "!! [4/6] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/6] walk green on a scratch copy of the live database (above)"
restore() {
  say "!! RED after placing - restoring byte-identically"
  [ -f "$FIN/day_resync.py.bak_S399_${FROM:0:8}" ] && \cp -p "$FIN/day_resync.py.bak_S399_${FROM:0:8}" "$FIN/day_resync.py"
  say "   day_resync.py $(m5 "$FIN/day_resync.py") · the database backup of this run: $FIN/finance.db.bak_S399_$STAMP"
  exit 1
}
"$SPY" - "$FIN/finance.db" "$FIN/finance.db.bak_S399_$STAMP" <<'PYEOF' || { say "!! [5/6] database backup failed - nothing installed"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
\cp -p "$FIN/day_resync.py" "$FIN/day_resync.py.bak_S399_${FROM:0:8}" || restore
\cp -p day_resync.py "$FIN/day_resync.py" && chmod 644 "$FIN/day_resync.py" || restore
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
[ "$(m5 "$FIN/day_resync.py")" = "$TO" ] || restore
say "[5/6] database backed up (finance.db.bak_S399_$STAMP); day_resync.py.bak_S399_${FROM:0:8} beside it; placed; md5 read back = the kit"
ROUT="$( cd "$FIN" && flock -w 120 /tmp/day_resync.lock "$VPY" -B day_resync.py 2>&1 )"
echo "$ROUT" | sed -n '/HOME\/PROC/,$p' | sed 's/^/   /'
echo "$ROUT" | grep -q "^summary2:" || restore
say "[6/6] $KIT: DONE -- first run above; the same cron line (# S356_DAY_TRUTH_2) runs it every 30 minutes. Open 23-Sep on the approvals page: Without cash 257 (home 62 + procedure 195)."
md5sum "$FIN/day_resync.py"
