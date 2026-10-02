#!/bin/bash
# =============================================================================
# install_S449_RECEPTION_UPLOAD.sh -- session 290, 02-Oct-2026 -- D659.
# THE OWNER, 02-Oct-2026: "One is direct upload from the reception PC to server."
#   NEW   /root/finance/reception_door.py    the door: POST /finance/api/reception/heartbeat and .../report,
#                                            each request signed (Ed25519) by a key made ON the reception PC
#   NEW   /root/finance/reception_keys.txt   that PC's PUBLIC key (no secret is in this kit or on this box)
#   EDIT  /root/finance/finance_app.py       four anchored edits on exact bytes (ac24fc5e): the two paths reach the door,
#                                            the door is mounted (guarded), /finance/health gains the row "Reception PC",
#                                            the mounts row counts 26 parts
# A report goes through docterz_pickup.take() (S443) -- the Drive pickup's own door -- so two roads count it once.
# Walked first on a scratch copy of /root/finance and of finance.db: the real app, and the reception agent's own code
# over real HTTP. Restarts clinic-finance; anything red after placing -> every file restored. No table is created, no
# setting written, nothing sent anywhere. DRY=1 runs every gate and the walk and places nothing.
# =============================================================================
set -u
KIT="S449_RECEPTION_UPLOAD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"; SVC="${SVC:-clinic-finance}"; BASEURL="${BASEURL:-http://127.0.0.1:8106}"
FROM=ac24fc5e4e312b0bf3718b42380d5e64; TO=022a9b0e3b0b22e748a1283d53c2c201
PICKUP=b2dc54758bc5fb7eb7550828eeb15d40
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s449_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$WALK"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/8] $SPY (the interpreter clinic-finance runs on) lacks flask - nothing installed"; exit 1; }
[ -f "$DBF" ] || { say "!! [1/8] $DBF is not there - nothing installed"; exit 1; }
NKEYS="$(grep -cE '^[0-9a-f]{64}([[:space:]]|$)' reception_keys.txt)"
[ "$NKEYS" -ge 1 ] || { say "!! [1/8] reception_keys.txt carries no public key - nothing installed"; exit 1; }
DOOR_TO="$(m5 built/reception_door.py)"; KEYS_TO="$(m5 reception_keys.txt)"
say "[1/8] kit gates green (SUMS, KIT_ID, flask on $SPY, finance.db, $NKEYS public key)"

if [ "$(m5 "$FIN/finance_app.py")" = "$TO" ] && [ "$(m5 "$FIN/reception_door.py")" = "$DOOR_TO" ] && [ "$(m5 "$FIN/reception_keys.txt")" = "$KEYS_TO" ]; then
  say "-- ALREADY INSTALLED: the three files are at the kit's pins; $SVC $(systemctl is-active "$SVC" 2>/dev/null)"; exit 0
fi
[ "$(m5 "$FIN/finance_app.py")" = "$FROM" ] || { say "!! [2/8] $FIN/finance_app.py is $(m5 "$FIN/finance_app.py"), not its FROM pin $FROM - someone changed it since the build; nothing installed"; exit 1; }
[ "$(m5 "$FIN/docterz_pickup.py")" = "$PICKUP" ] || { say "!! [2/8] $FIN/docterz_pickup.py is $(m5 "$FIN/docterz_pickup.py"), not the S443 bytes $PICKUP this door was walked with - nothing installed"; exit 1; }
[ ! -e "$FIN/reception_door.py" ] || { say "!! [2/8] $FIN/reception_door.py already exists - nothing installed"; exit 1; }
[ ! -e "$FIN/reception_keys.txt" ] || { say "!! [2/8] $FIN/reception_keys.txt already exists - nothing installed"; exit 1; }
say "[2/8] finance_app.py at its FROM pin; docterz_pickup.py is the S443 file; the door and its key file are not there yet"

"$SPY" -m py_compile built/reception_door.py apply_s449.py walk_s449.py reception/reception_agent.py 2>/dev/null || { say "!! [3/8] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/8] compiles on $SPY"

for side in new old; do
  mkdir -p "$WALK/$side/finance_ui" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null; cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/" 2>/dev/null
  [ -d "$FIN/spine" ] && { mkdir -p "$WALK/$side/spine"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; }
done
cp -p built/reception_door.py "$WALK/new/" && "$SPY" -B apply_s449.py "$WALK/new/finance_app.py" >/dev/null
[ "$(m5 "$WALK/new/finance_app.py")" = "$TO" ] || { say "!! [4/8] the patched copy is not the predicted bytes $TO - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile "$WALK/new/finance_app.py" 2>/dev/null || { say "!! [4/8] the patched finance_app.py does not compile - nothing installed"; clean; exit 1; }
copydb "$DBF" "$WALK/scratch_fin.db" || { say "!! [4/8] no scratch copy of finance.db - nothing installed"; clean; exit 1; }
WOUT="$( cd "$WALK" && FINANCE_SSO_DIR="$POR" timeout 900 "$SPY" -B "$KDIR/walk_s449.py" --new "$WALK/new" --old "$WALK/old" --db "$WALK/scratch_fin.db" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^   FAILED|^WALK_S449|^-- (new|old) probe' | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S449 GREEN" || { say "!! [4/8] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
say "[4/8] walk green on scratch copies: $(echo "$WOUT" | grep '^WALK_S449 NEW' | sed 's/WALK_S449 NEW //') · the box as it is refuses the door, as it must"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BAK="$FIN/finance_app.py.bak_S449_ac24fc5e"
\cp -p "$FIN/finance_app.py" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [5/8] backup failed - nothing placed"; clean; exit 1; }
say "[5/8] backup: $BAK"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BAK" "$FIN/finance_app.py"; rm -f "$FIN/reception_door.py" "$FIN/reception_keys.txt"
  systemctl restart "$SVC" 2>/dev/null || true; sleep 7
  say "   $FIN/finance_app.py $(m5 "$FIN/finance_app.py") (the FROM bytes) · the door and its key file removed · $SVC $(systemctl is-active "$SVC" 2>/dev/null) · healthz $(health "$BASEURL/finance/healthz")"
  clean; exit 1
}
\cp -p built/reception_door.py "$FIN/reception_door.py" || restore "copy the door"
\cp -p reception_keys.txt "$FIN/reception_keys.txt" || restore "copy the key file"
chmod 644 "$FIN/reception_door.py" "$FIN/reception_keys.txt"
"$SPY" -B apply_s449.py "$FIN/finance_app.py" | sed 's/^/      /'
[ "$(m5 "$FIN/finance_app.py")" = "$TO" ] && [ "$(m5 "$FIN/reception_door.py")" = "$DOOR_TO" ] && [ "$(m5 "$FIN/reception_keys.txt")" = "$KEYS_TO" ] || restore "md5 read-back"
say "[6/8] placed; all three md5s read back = the kit's pins"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart $SVC"
sleep 7
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health "$BASEURL/finance/healthz"); [ "$c1" = 200 ] || restore "healthz $c1"
D1="$(curl -s -m 10 -X POST -H 'Content-Type: application/octet-stream' --data-binary '{}' "$BASEURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the door did not answer an unsigned request with its own refusal: $(echo "$D1" | cut -c1-160)"
c3=$(health "$BASEURL/finance/health"); case "$c3" in 302|401) ;; *) restore "/finance/health answered $c3 without a login";; esac
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
JR="$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError')"
[ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s)"
say "[7/8] $SVC active · healthz 200 · the door refuses an unsigned request itself (NOT_YOU) · /finance/health $c3 (the login gate) · journal clean"

say "[8/8] waiting for the reception PC's next report (it posts every 5 minutes; up to 6 minutes) ..."
HB="$FIN/reception_heartbeat.json"; i=0
while [ $i -lt 36 ] && [ ! -s "$HB" ]; do sleep 10; i=$((i+1)); done
if [ -s "$HB" ]; then
  "$SPY" -c "
import json,sys
r=json.load(open(sys.argv[1])); b=r.get('beat',{})
print('      ARRIVED %s from %s: agent %s on %s, Google Drive %s, attention: %s' % (r.get('received_ist'), r.get('from'), b.get('agent_version'), b.get('computer'), 'running' if b.get('google_drive_running') else 'NOT running', '; '.join(b.get('attention') or []) or 'nothing'))" "$HB"
  sleep 20
  "$SPY" -c "
import sqlite3,sys
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
try:
    rows=c.execute(\"SELECT kind,business_date,rows,status FROM docterz_export WHERE drive_id LIKE 'reception:%' ORDER BY id DESC LIMIT 6\").fetchall()
except Exception as ex:
    rows=[]
print('      Docterz reports by the direct road so far: %s' % (', '.join('%s %s (%d rows, %s)'%r for r in rows) or 'none yet -- the PC sends one when reception next downloads it'))" "$DBF"
else
  say "      no heartbeat yet -- the reception PC may be switched off or logged out; the first one lands by itself when it is on."
fi
clean
say "all green -- $KIT: DONE. The reception PC now reports straight to this server; /finance/health carries the row 'Reception PC'."
md5sum "$FIN/finance_app.py" "$FIN/reception_door.py" "$FIN/reception_keys.txt"
