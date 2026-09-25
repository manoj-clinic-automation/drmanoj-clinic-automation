#!/bin/bash
# =============================================================================
#  install_S398_SLIP_DEAD_CODE.sh · kit S398_SLIP_DEAD_CODE (session 282, 25-Sep-2026)
#
#  The drift read of slip_log.py found 157 lines nobody can reach, all left by S379's retirement of the Docterz-upload
#  screen. This deletes them and nothing else: every page stays byte-identical (proved on two scratch copies of the
#  live database before anything is placed).
#  FILE:  /root/finance/slip_log.py  S392 ffb629c1 -> S398 d208f57a.  Restarts clinic-finance only.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S398_SLIP_DEAD_CODE/install_S398_SLIP_DEAD_CODE.sh
# =============================================================================
set -u
KIT="S398_SLIP_DEAD_CODE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"; DBF="${FINANCE_DB:-$FIN/finance.db}"; FPORT="${FIN_PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s398_walk_$STAMP"
S_FROM=ffb629c1b4dd3220053d2ecf02d5d6b1; S_TO=d208f57a4070b5acc02e3e91c7cb86bd
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
code() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 slip_log.py)" = "$S_TO" ] || { say "!! [1/6] kit slip_log.py not at its pin - nothing installed"; exit 1; }
say "[1/6] kit gates green"
[ "$(m5 "$FIN/slip_log.py")" = "$S_TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
[ "$(m5 "$FIN/slip_log.py")" = "$S_FROM" ] || { say "!! [2/6] slip_log.py is $(m5 "$FIN/slip_log.py"), not S392 - nothing installed"; exit 1; }
say "[2/6] live pin exact (slip_log S392)"
mkdir -p "$WALK" || exit 1
"$VPY" -B -c "import sys, hashlib; sys.argv = sys.argv[1:]; exec(open(sys.argv[0]).read().split('open(sys.argv[2]')[0]); assert hashlib.md5(out.encode()).hexdigest() == sys.argv[2]" \
  apply_s398.py "$FIN/slip_log.py" "$S_TO" 2>/dev/null || { say "!! [3/6] the kit file is not the live file minus the dead code - nothing installed"; rm -rf "$WALK"; exit 1; }
"$VPY" -B -m py_compile slip_log.py walk_s398.py || { say "!! [3/6] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/6] rebuilt from the live bytes = the kit file; py_compile green"
for X in A B; do
  "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/scratch_$X.db" \
    || { say "!! [4/6] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
done
WOUT="$( cd /tmp && timeout 240 "$VPY" -B "$KDIR/walk_s398.py" "$KDIR/slip_log.py" "$FIN/slip_log.py" "$WALK/scratch_A.db" "$WALK/scratch_B.db" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/6] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/6] $WOUT"
BS="$FIN/slip_log.py.bak_S398_ffb629c1"
\cp -p "$FIN/slip_log.py" "$BS" || { say "!! [5/6] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing (${1:-a check failed}) - restoring byte-identically"
  \cp -p "$BS" "$FIN/slip_log.py"; systemctl restart clinic-finance || true; sleep 5
  say "   slip_log $(m5 "$FIN/slip_log.py") · finance $(code "http://127.0.0.1:$FPORT/finance/healthz")"; exit 1
}
\cp -p slip_log.py "$FIN/slip_log.py" && [ "$(m5 "$FIN/slip_log.py")" = "$S_TO" ] || restore "slip_log.py did not read back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "clinic-finance would not restart"
sleep 5; systemctl is-active --quiet clinic-finance || restore "clinic-finance not active after restart"
H=$(code "http://127.0.0.1:$FPORT/finance/healthz"); PC=$(code "http://127.0.0.1:$FPORT/finance/slips/api/pending-counts")
NX=$(code -X POST -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$FPORT/finance/slips/api/lab-noid")
[ "$H" = 200 ] || restore "finance healthz answered $H"
{ [ "$PC" = 302 ] || [ "$PC" = 401 ] || [ "$PC" = 403 ]; } || restore "the counts door without login answered $PC"
{ [ "$NX" = 302 ] || [ "$NX" = 401 ]; } || restore "the lab-noid door without its token answered $NX"
J="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null)"
echo "$J" | grep -q "slip_log NOT mounted" && restore "$(echo "$J" | grep -m1 "slip_log NOT mounted" | cut -c1-200)"
echo "$J" | grep -q 'slip_log.py", line' && restore "a fault inside slip_log.py: $(echo "$J" | grep -m1 -A1 'slip_log.py", line' | tail -1 | cut -c1-160)"
say "[5/6] placed; finance healthz $H · counts door without login $PC · lab-noid door without token $NX (both locked) · backup beside the file"
md5sum "$FIN/slip_log.py"
say "[6/6] $KIT: DONE -- nothing looks different; slip_log.py is 157 lines shorter"
