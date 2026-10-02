#!/bin/bash
# =============================================================================
# install_S453_RECEPTION_SERVER_DOOR.sh -- session 290, 02-Oct-2026 -- D661.
# THE SECOND JOB DOOR for the reception PC: its only one ran through Google Drive, which is what failed there on 01-Oct.
#   REPLACE /root/finance/reception_door.py      dfd557bc (S449) -> this kit's: five paths under /finance/api/reception/jobs/
#   EDIT    /root/finance/finance_app.py         e8dbf77e (S450) -> a92baae4: those five paths join PUBLIC_PATHS, nothing else
#   NEW     /root/finance/reception_job_keys.txt the PUBLIC key whose signature lets a job into the queue (the owner's PC holds the secret)
#   NOT TOUCHED: pc_kits.py (7889600c), the portal. The queue /root/finance/reception_jobs/ is made at the first job (mode 700).
# The server only relays: the PC verifies every job again with its own key list, so this server cannot make it run anything.
# The PC's side (agent S453.1) is in deploy_kits/PC_KITS/reception/kit.zip and goes to the PC by a signed job afterwards.
# Walked first on a scratch copy of /root/finance and finance.db with the kit's own agent over real HTTP.
# Restarts clinic-finance only; anything red after placing -> both files put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S453_RECEPTION_SERVER_DOOR"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; POR="$ROOT/portal"
KITS="${KITS:-$(cd "$KDIR/.." && pwd)/PC_KITS}"
DBF="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
APP_FROM=e8dbf77e8a4dbd3dd83486ed6ebf68a5; APP_TO=a92baae43afbdd92c36930535418ad58
DOOR_FROM=dfd557bcae7e2712e6d1e9a8b86d68f5
PCKITS=7889600c3f32db1e80df5578fbe99f28
KITZIP=90e8e94ed935b26d0c00a9030c217da2; PYZIP=30a7b6ab01fbaa598844f4b3d8220a68
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s453_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$WALK"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/8] $SPY lacks flask - nothing installed"; exit 1; }
[ -f "$DBF" ] || { say "!! [1/8] $DBF is not there - nothing installed"; exit 1; }
[ "$(m5 "$KITS/reception/kit.zip")" = "$KITZIP" ] && [ "$(m5 "$KITS/_shared/pyportable_3.11.9.zip")" = "$PYZIP" ] && grep -q "^kit_md5=$KITZIP$" "$KITS/reception/KIT_INFO.txt" \
  || { say "!! [1/8] the Reception PC's kit in $KITS is not the one this kit was walked with (agent S453.1) - nothing installed"; exit 1; }
DOOR_TO="$(m5 built/reception_door.py)"; JK_TO="$(m5 built/reception_job_keys.txt)"
say "[1/8] kit gates green (SUMS, KIT_ID, flask, finance.db, the Reception PC's kit with agent S453.1 in the repository clone)"

if [ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] && [ "$(m5 "$FIN/reception_door.py")" = "$DOOR_TO" ] && [ "$(m5 "$FIN/reception_job_keys.txt")" = "$JK_TO" ]; then
  say "-- ALREADY INSTALLED: all three files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [2/8] $FIN/finance_app.py is $(m5 "$FIN/finance_app.py"), not the S450 pin $APP_FROM - someone changed it since the build; nothing installed"; exit 1; }
[ "$(m5 "$FIN/reception_door.py")" = "$DOOR_FROM" ] || { say "!! [2/8] $FIN/reception_door.py is $(m5 "$FIN/reception_door.py"), not the S449 file $DOOR_FROM - nothing installed"; exit 1; }
[ "$(m5 "$FIN/pc_kits.py")" = "$PCKITS" ] || { say "!! [2/8] $FIN/pc_kits.py is not the S451 file - install S451 first; nothing installed"; exit 1; }
[ ! -e "$FIN/reception_job_keys.txt" ] || [ "$(m5 "$FIN/reception_job_keys.txt")" = "$JK_TO" ] || { say "!! [2/8] $FIN/reception_job_keys.txt is there and is not this kit's - nothing installed"; exit 1; }
HADJK=0; [ -e "$FIN/reception_job_keys.txt" ] && HADJK=1
say "[2/8] finance_app.py (S450), reception_door.py (S449) and pc_kits.py (S451) at their pins"

"$SPY" -m py_compile built/reception_door.py apply_s453.py walk_s453.py 2>/dev/null || { say "!! [3/8] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/8] compiles"

for side in new old; do
  mkdir -p "$WALK/$side/finance_ui" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null; cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/" 2>/dev/null
  [ -d "$FIN/spine" ] && { mkdir -p "$WALK/$side/spine"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; }
  rm -f "$WALK/$side/reception_heartbeat.json" "$WALK/$side/pc_kit_codes.json"
done
mkdir -p "$WALK/sso"
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$WALK/sso/"; done   # never the live secret, never the user store
\cp -p built/reception_door.py "$WALK/new/reception_door.py" && "$SPY" -B apply_s453.py "$WALK/new/finance_app.py" >/dev/null
[ "$(m5 "$WALK/new/finance_app.py")" = "$APP_TO" ] && [ "$(m5 "$WALK/new/reception_door.py")" = "$DOOR_TO" ] && [ "$(m5 "$WALK/old/reception_door.py")" = "$DOOR_FROM" ] \
  || { say "!! [4/8] a scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile "$WALK/new/finance_app.py" 2>/dev/null || { say "!! [4/8] the patched finance_app.py does not compile - nothing installed"; clean; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
copydb "$DBF" "$WALK/scratch_fin.db" || { say "!! [4/8] no scratch copy of finance.db - nothing installed"; clean; exit 1; }
WOUT="$( cd "$WALK" && timeout 1200 "$SPY" -B "$KDIR/walk_s453.py" --new "$WALK/new" --old "$WALK/old" --sso "$WALK/sso" --db "$WALK/scratch_fin.db" --kits "$KITS" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^   FAILED|^WALK_S453|^-- old: WALK_S453|probe exit' | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S453 GREEN" || { say "!! [4/8] walk red - nothing installed"; echo "$WOUT" | tail -30 | cut -c1-400; clean; exit 1; }
say "[4/8] walk green on scratch copies (the five doors, the kit's own agent fetching, verifying, running and answering over HTTP, the PC refusing what only the server vouches for); the box as it is has no such door, as it must"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S453_$(echo "$APP_FROM" | cut -c1-8)"; BD="$FIN/reception_door.py.bak_S453_$(echo "$DOOR_FROM" | cut -c1-8)"
\cp -p "$FIN/finance_app.py" "$BA" && [ "$(m5 "$BA")" = "$APP_FROM" ] && \cp -p "$FIN/reception_door.py" "$BD" && [ "$(m5 "$BD")" = "$DOOR_FROM" ] || { say "!! [5/8] a backup failed - nothing placed"; clean; exit 1; }
say "[5/8] backups: .bak_S453_<from8> beside finance_app.py and reception_door.py"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$FIN/finance_app.py"; \cp -p "$BD" "$FIN/reception_door.py"; [ "$HADJK" = 1 ] || rm -f "$FIN/reception_job_keys.txt"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   finance_app.py $(m5 "$FIN/finance_app.py") · reception_door.py $(m5 "$FIN/reception_door.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
\cp -p built/reception_job_keys.txt "$FIN/reception_job_keys.txt" || restore "copy reception_job_keys.txt"; chmod 644 "$FIN/reception_job_keys.txt"
\cp -p built/reception_door.py "$FIN/reception_door.py" || restore "copy reception_door.py"; chmod 644 "$FIN/reception_door.py"
"$SPY" -B apply_s453.py "$FIN/finance_app.py" | sed 's/^/      /'
[ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] || restore "md5 read-back of finance_app.py"
[ "$(m5 "$FIN/reception_door.py")" = "$DOOR_TO" ] || restore "md5 read-back of reception_door.py"
[ "$(m5 "$FIN/reception_job_keys.txt")" = "$JK_TO" ] || restore "md5 read-back of reception_job_keys.txt"
[ "$(m5 "$FIN/pc_kits.py")" = "$PCKITS" ] || restore "pc_kits.py changed under the install"
say "[6/8] placed; all three md5s read back = the kit's pins"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/pcs"); case "$c2" in 302|401) ;; *) restore "/finance/pcs answered $c2 without a login";; esac
D1="$(curl -s -m 10 -X POST -H 'Content-Type: application/json' --data-binary '{"name":"x"}' "$FINURL/finance/api/reception/jobs/submit")"
echo "$D1" | grep -q '"REFUSED"' || restore "the submit door did not answer with its own refusal: $(echo "$D1" | cut -c1-160)"
D2="$(curl -s -m 10 -X POST --data-binary '' "$FINURL/finance/api/reception/jobs/next")"
echo "$D2" | grep -q '"NOT_YOU"' || restore "the PC's door did not refuse an unsigned request: $(echo "$D2" | cut -c1-160)"
D3="$(curl -s -m 10 -X POST -H 'Content-Type: application/json' --data-binary '{"name":"x"}' "$FINURL/finance/api/reception/jobs/read")"
echo "$D3" | grep -q '"NOT_YOU"' || restore "the read door did not refuse an unsigned read: $(echo "$D3" | cut -c1-160)"
D4="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D4" | grep -q '"NOT_YOU"' || restore "the heartbeat door (S449) no longer answers"
D5="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D5" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[7/8] clinic-finance active · healthz 200 · submit, next and read each refuse an unsigned request in their own words · the heartbeat door and the kit door still answer · /finance/pcs $c2 (the login gate) · journal clean"

sleep 20
HBAGE="$("$SPY" -c "
import json,sys,time
try:
    r=json.load(open(sys.argv[1])); print('%d minute(s) ago, agent %s' % ((time.time()-r['received_ts'])/60, r['beat'].get('agent_version')))
except Exception as ex:
    print('not read (%s)' % ex)" "$FIN/reception_heartbeat.json")"
say "[8/8] the reception PC's last direct report: $HBAGE (it takes agent S453.1 by a signed job next - nothing for you to do)"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py" "$FIN/reception_door.py" "$FIN/reception_job_keys.txt" "$FIN/pc_kits.py"
