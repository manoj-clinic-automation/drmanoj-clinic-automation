#!/bin/bash
# =============================================================================
# install_S456_WINDOWS_CURRENCY.sh -- session 292, 03-Oct-2026 -- F-700; and F-694: the first of the parent's
# installers to take the server-wide build lock.
# THE RECEPTION PC ROW OF THE HEALTH PAGE SAYS TWO THINGS IT DID NOT:
#   REPLACE /root/finance/reception_door.py   d0a79231 (S453) -> this kit's.
#     1. BOTH Docterz reports by name (the owner, 03-Oct: "you have only mentioned the consultation report"): the
#        consultation report AND the follow-up log, each with the time it was last downloaded at reception; amber the
#        next morning when a clinic evening was missed for either. (The follow-up log went undownloaded from 7 July to
#        2 October and this row never said so.) Works with the agent the PC already runs.
#     2. How current the PC's Windows is, in the PC's own words ("... last updated Sep 2026"); when no cumulative
#        update has gone in for 75 days the row moves to "Worth knowing" and says since when. Never a warning: it is a
#        decision for the owner, told once (F-700). These words need agent S456.1 on the PC.
#   NOT TOUCHED: finance_app.py, pc_kits.py, the portal, the database, the doors' own code. No setting is written
#           (reception.windows_stale_days and reception.report_missed_evenings are read if someone sets them; 75 and 1 if not).
# The PC's side (agent S456.1: three registry keys and one file's date, read every six hours) is in
# deploy_kits/PC_KITS/reception/kit.zip, which this line's git pull brings, and goes to the PC by a signed job
# afterwards. Until that job the row carries the two reports and no Windows words.
# Walked on the kit's file beside the live one with made-up heartbeats in /tmp; nothing live is read by the walk.
# Restarts clinic-finance only (about 8 seconds); anything red after placing -> the file put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S456_WINDOWS_CURRENCY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
KITS="${KITS:-$(cd "$KDIR/.." && pwd)/PC_KITS}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
DOOR_FROM=d0a7923191496eed211811d0c13f7efd
KITZIP=59a4483681fe320ca27b47197343eb8d; PYZIP=30a7b6ab01fbaa598844f4b3d8220a68
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask - nothing installed"; exit 1; }
[ "$(m5 "$KITS/reception/kit.zip")" = "$KITZIP" ] && [ "$(m5 "$KITS/_shared/pyportable_3.11.9.zip")" = "$PYZIP" ] && grep -q "^kit_md5=$KITZIP$" "$KITS/reception/KIT_INFO.txt" \
  || { say "!! [1/7] the Reception PC's kit in $KITS is not the one this kit was built with (agent S456.1) - nothing installed"; exit 1; }
DOOR_TO="$(m5 built/reception_door.py)"
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/7] kit gates green (SUMS, KIT_ID, flask, the Reception PC's kit with agent S456.1 in the repository clone); the build lock is taken"

if [ "$(m5 "$FIN/reception_door.py")" = "$DOOR_TO" ]; then
  say "-- ALREADY INSTALLED: reception_door.py is at the kit's pin; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
if grep -q '^def windows_note(' "$FIN/reception_door.py" 2>/dev/null && grep -q '^def reports_note(' "$FIN/reception_door.py" 2>/dev/null; then
  say "-- ALREADY INSTALLED: reception_door.py is a later kit's file ($(m5 "$FIN/reception_door.py" | cut -c1-8)) that carries this kit's change; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
[ "$(m5 "$FIN/reception_door.py")" = "$DOOR_FROM" ] || { say "!! [2/7] $FIN/reception_door.py is $(m5 "$FIN/reception_door.py"), not the S453 file $DOOR_FROM - someone changed it since the build; nothing installed"; exit 1; }
say "[2/7] reception_door.py at its S453 pin"

"$SPY" -m py_compile built/reception_door.py walk_s456.py 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
clean
say "[3/7] compiles"

WOUT="$( cd /tmp && timeout 300 "$SPY" -B "$KDIR/walk_s456.py" --new "$KDIR/built/reception_door.py" --old "$FIN/reception_door.py" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^   FAILED|^WALK_S456' | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S456 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -30 | cut -c1-400; clean; exit 1; }
say "[4/7] walk green: the trouble rows read as before; both Docterz reports are named with the time each was last downloaded; the Windows words appear only when the PC sends them"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BD="$FIN/reception_door.py.bak_S456_$(echo "$DOOR_FROM" | cut -c1-8)"
\cp -p "$FIN/reception_door.py" "$BD" && [ "$(m5 "$BD")" = "$DOOR_FROM" ] || { say "!! [5/7] the backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backup: $BD"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BD" "$FIN/reception_door.py"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   reception_door.py $(m5 "$FIN/reception_door.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
\cp -p built/reception_door.py "$FIN/reception_door.py" || restore "copy reception_door.py"; chmod 644 "$FIN/reception_door.py"
[ "$(m5 "$FIN/reception_door.py")" = "$DOOR_TO" ] || restore "md5 read-back of reception_door.py"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
D2="$(curl -s -m 10 -X POST --data-binary '' "$FINURL/finance/api/reception/jobs/next")"
echo "$D2" | grep -q '"NOT_YOU"' || restore "the PC's job door no longer refuses an unsigned request: $(echo "$D2" | cut -c1-160)"
D3="$(curl -s -m 10 -X POST -H 'Content-Type: application/json' --data-binary '{"name":"x"}' "$FINURL/finance/api/reception/jobs/submit")"
echo "$D3" | grep -q '"REFUSED"' || restore "the submit door did not answer with its own refusal: $(echo "$D3" | cut -c1-160)"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pin · clinic-finance active · healthz 200 · the heartbeat, job and kit doors answer as before · journal clean"

ROWNOW="$("$SPY" -B -c "
import importlib.util, os, sys
os.environ['RECEPTION_BEAT'] = sys.argv[2]
s = importlib.util.spec_from_file_location('rd_now', sys.argv[1]); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
got = []
m.health_row(lambda k, l, st, d, h='': got.append((st, d)), lambda con, k, d=None: d, None)
print('%s -- %s' % got[0])" "$FIN/reception_door.py" "$FIN/reception_heartbeat.json" 2>&1 | tail -1)"
say "[7/7] the Reception PC row as the health page reads it now: $ROWNOW"
say "      (the Windows words join it once the PC has agent S456.1 - by a signed job, nothing for you to do)"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/reception_door.py"
