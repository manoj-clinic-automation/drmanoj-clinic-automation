#!/bin/bash
# =============================================================================
# install_S457_DOCTERZ_SERVER_PATH.sh -- session 292, 03-Oct-2026 -- F-697's remedy, at the owner's word:
# "also need the exports from reception pc docterz for this, server path seems better than the google drive one".
# THE OWNER'S PC READS RECEPTION'S TWO DOCTERZ EXPORTS BACK FROM THIS SERVER -- the consultation report AND the
# follow-up log -- so the follow-up tracker there no longer waits on Google Drive or on a copy line each evening.
#   REPLACE /root/finance/reception_door.py   be5ec171 (S456) -> this kit's: two read doors,
#           POST /finance/api/reception/exports/list and .../exports/get, each opened only by a fresh Ed25519 signature
#           from the key in reception_job_keys.txt (the owner's PC holds the only secret), over that door's own words.
#   EDIT    /root/finance/finance_app.py      a92baae4 (S453) -> 40aef4df: those two paths join PUBLIC_PATHS, nothing else.
#   NOT TOUCHED: docterz_pickup.py (S443: it still takes, files and keeps the exports), the database's rows, pc_kits.py,
#           the portal. No setting is written. S456 must be in first (the same line runs it).
# The PC's side (pc/docterz_fetch.py and one line in DOCTERZ_PICKUP.bat) is placed on the owner's PC by the assistant
# after this line is green; until then nothing asks these doors anything.
# Walked first: the kit's door and the PC's fetcher end to end over real HTTP on made-up exports in /tmp, with the
# server's own docterz_pickup.py filing them. Nothing live is read by the walk.
# Restarts clinic-finance only (about 8 seconds); anything red after placing -> both files put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S457_DOCTERZ_SERVER_PATH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
DBF="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
APP_FROM=a92baae43afbdd92c36930535418ad58; APP_TO=40aef4dfe976a596c81be46da1fbb429
DOOR_FROM=be5ec1712837802676e01e2e6fea7990; DOOR_S453=d0a7923191496eed211811d0c13f7efd
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s457_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/8] $SPY lacks flask - nothing installed"; exit 1; }
DOOR_TO="$(m5 built/reception_door.py)"
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/8] kit gates green (SUMS, KIT_ID, flask); the build lock is taken"

if [ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] && [ "$(m5 "$FIN/reception_door.py")" = "$DOOR_TO" ]; then
  say "-- ALREADY INSTALLED: both files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
if [ "$(m5 "$FIN/reception_door.py")" = "$DOOR_S453" ]; then
  say "!! [2/8] $FIN/reception_door.py is still the S453 file - install S456_WINDOWS_CURRENCY first (the owner's line runs it before this one); nothing installed"; exit 1; fi
[ "$(m5 "$FIN/reception_door.py")" = "$DOOR_FROM" ] || { say "!! [2/8] $FIN/reception_door.py is $(m5 "$FIN/reception_door.py"), not the S456 file $DOOR_FROM - someone changed it since the build; nothing installed"; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APP_FROM" ] || { say "!! [2/8] $FIN/finance_app.py is $(m5 "$FIN/finance_app.py"), not the S453 pin $APP_FROM - someone changed it since the build; nothing installed"; exit 1; }
[ -f "$FIN/docterz_pickup.py" ] || { say "!! [2/8] $FIN/docterz_pickup.py (S443) is not there - nothing installed"; exit 1; }
[ -f "$DBF" ] || { say "!! [2/8] $DBF is not there - nothing installed"; exit 1; }
NK="$(grep -c -E '^[0-9a-fA-F]{64}([[:space:]]|$)' "$FIN/reception_job_keys.txt" 2>/dev/null)"
[ "${NK:-0}" -ge 1 ] || { say "!! [2/8] $FIN/reception_job_keys.txt holds no key - the doors would open to nobody; nothing installed"; exit 1; }
say "[2/8] reception_door.py (S456) and finance_app.py (S453) at their pins; the Docterz reader (S443) and $NK key(s) are here"

mkdir -p "$SCR" && \cp -p "$FIN/finance_app.py" "$SCR/finance_app.py" || { say "!! [3/8] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s457.py "$SCR/finance_app.py" >/dev/null
[ "$(m5 "$SCR/finance_app.py")" = "$APP_TO" ] || { say "!! [3/8] the edited scratch copy of finance_app.py is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile built/reception_door.py apply_s457.py walk_s457.py pc/docterz_fetch.py "$SCR/finance_app.py" 2>/dev/null || { say "!! [3/8] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/8] compiles; the one edit to finance_app.py gives the predicted bytes on a scratch copy"

WOUT="$( cd /tmp && timeout 600 "$SPY" -B "$KDIR/walk_s457.py" --door "$KDIR/built/reception_door.py" --fetch "$KDIR/pc/docterz_fetch.py" --finance "$FIN" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^   FAILED|^WALK_S457' | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S457 GREEN" || { say "!! [4/8] walk red - nothing installed"; echo "$WOUT" | grep -v 'HTTP/1.1' | tail -30 | cut -c1-400; clean; exit 1; }
say "[4/8] walk green: the doors open only to the owner's PC's signature; the fetcher brings both reports byte for byte, never twice, and never raises"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/finance_app.py.bak_S457_$(echo "$APP_FROM" | cut -c1-8)"; BD="$FIN/reception_door.py.bak_S457_$(echo "$DOOR_FROM" | cut -c1-8)"
\cp -p "$FIN/finance_app.py" "$BA" && [ "$(m5 "$BA")" = "$APP_FROM" ] && \cp -p "$FIN/reception_door.py" "$BD" && [ "$(m5 "$BD")" = "$DOOR_FROM" ] || { say "!! [5/8] a backup failed - nothing placed"; clean; exit 1; }
say "[5/8] backups: .bak_S457_<from8> beside finance_app.py and reception_door.py"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$FIN/finance_app.py"; \cp -p "$BD" "$FIN/reception_door.py"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   finance_app.py $(m5 "$FIN/finance_app.py") · reception_door.py $(m5 "$FIN/reception_door.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
\cp -p built/reception_door.py "$FIN/reception_door.py" || restore "copy reception_door.py"; chmod 644 "$FIN/reception_door.py"
"$SPY" -B apply_s457.py "$FIN/finance_app.py" | sed 's/^/      /'
[ "$(m5 "$FIN/finance_app.py")" = "$APP_TO" ] || restore "md5 read-back of finance_app.py"
[ "$(m5 "$FIN/reception_door.py")" = "$DOOR_TO" ] || restore "md5 read-back of reception_door.py"
say "[6/8] placed; both md5s read back = the kit's pins"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/pcs"); case "$c2" in 302|401) ;; *) restore "/finance/pcs answered $c2 without a login";; esac
E1="$(curl -s -m 10 -X POST -H 'Content-Type: application/json' --data-binary '{}' "$FINURL/finance/api/reception/exports/list")"
echo "$E1" | grep -q '"NOT_YOU"' || restore "the list door did not refuse an unsigned question in its own words: $(echo "$E1" | cut -c1-160)"
E2="$(curl -s -m 10 -X POST -H 'Content-Type: application/json' --data-binary '{"md5":"00000000000000000000000000000000"}' "$FINURL/finance/api/reception/exports/get")"
echo "$E2" | grep -q '"NOT_YOU"' || restore "the get door did not refuse an unsigned request in its own words: $(echo "$E2" | cut -c1-160)"
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
D2="$(curl -s -m 10 -X POST --data-binary '' "$FINURL/finance/api/reception/jobs/next")"
echo "$D2" | grep -q '"NOT_YOU"' || restore "the PC's job door no longer refuses an unsigned request: $(echo "$D2" | cut -c1-160)"
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[7/8] clinic-finance active · healthz 200 · the two new doors refuse an unsigned request in their own words · the heartbeat, job and kit doors answer as before · /finance/pcs $c2 (the login gate) · journal clean"

HELD="$("$SPY" -B -c "
import sqlite3, sys
try:
    c = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True)
    rows = c.execute(\"SELECT kind, business_date, rows FROM docterz_export WHERE status='current' AND stored<>'' ORDER BY taken_at DESC, id DESC LIMIT 4\").fetchall()
    print('; '.join('%s for %s (%s rows)' % r for r in rows) or 'none yet')
except Exception as ex:
    print('not read (%s)' % ex)" "$DBF" 2>&1 | tail -1)"
say "[8/8] the newest exports this server holds for the owner's PC to fetch: $HELD"
say "      (the owner's PC starts asking once its side is placed - by the assistant, nothing for you to do)"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/finance_app.py" "$FIN/reception_door.py"
