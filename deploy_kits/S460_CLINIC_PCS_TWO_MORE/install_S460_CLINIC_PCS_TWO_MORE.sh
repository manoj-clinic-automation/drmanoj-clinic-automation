#!/bin/bash
# =============================================================================
# install_S460_CLINIC_PCS_TWO_MORE.sh -- session 292, 03-Oct-2026 -- the owner: "do the housekeeping part for the
# medical PC first and then for the clinic PC tile".
# THE CLINIC PCs PAGE GETS TWO MORE BUTTONS: the Medical PC and Dr Manoj's own PC.
#   REPLACE /root/finance/pc_kits.py   7889600c (S451) -> this kit's: a second setup-file template (it fetches the
#           kit, checks it, and runs the kit's own setup_pc.py, which ONLY PUTS BACK WHAT IS NOT THERE), two entries
#           in SETUPS, and for each of the two PCs its file name and its "only a person can do these" list.
#           The Reception PC's entry, template, code door, enrol door and guard are byte for byte what they were.
#   COMES WITH THE PULL: deploy_kits/PC_KITS/medical/ and /manojz/ (kit.zip + KIT_INFO.txt), built by S458 and S459.
#   NOT TOUCHED: finance_app.py, reception_door.py, the portal, the tile grants, the database.
# Nothing is placed on any PC by this line: a button only hands out a file when the owner presses it on that PC.
# Walked first on scratch copies of the kits with made-up logins. Restarts clinic-finance only (about 8 seconds);
# anything red after placing -> the file put back. DRY=1 places nothing. Takes the build lock (F-694).
# =============================================================================
set -u
KIT="S460_CLINIC_PCS_TWO_MORE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
KITS="${KITS:-$(cd "$KDIR/.." && pwd)/PC_KITS}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
PCK_FROM=7889600c3f32db1e80df5578fbe99f28
K_REC=59a4483681fe320ca27b47197343eb8d; K_MED=83922881945b0cfd02da6fae808eee74; K_MAN=07f124f8c34188ca8b080c66f3bc2138; PYZIP=30a7b6ab01fbaa598844f4b3d8220a68
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
whole() { [ "$(m5 "$KITS/$1/kit.zip")" = "$2" ] && grep -q "^kit_md5=$2$" "$KITS/$1/KIT_INFO.txt" && grep -q "^python_md5=$PYZIP$" "$KITS/$1/KIT_INFO.txt"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask - nothing installed"; exit 1; }
[ "$(m5 "$KITS/_shared/pyportable_3.11.9.zip")" = "$PYZIP" ] || { say "!! [1/7] the Python part in $KITS/_shared is not the one the kits name - nothing installed"; exit 1; }
for pair in "reception:$K_REC" "medical:$K_MED" "manojz:$K_MAN"; do
  whole "${pair%%:*}" "${pair##*:}" || { say "!! [1/7] the ${pair%%:*} kit in $KITS is not the one this kit was walked with - nothing installed"; exit 1; }
done
PCK_TO="$(m5 built/pc_kits.py)"
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/7] kit gates green (SUMS, KIT_ID, flask; the three PCs' kits and the Python part in the repository clone are whole); the build lock is taken"

if [ "$(m5 "$FIN/pc_kits.py")" = "$PCK_TO" ]; then
  say "-- ALREADY INSTALLED: pc_kits.py is at the kit's pin; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
[ "$(m5 "$FIN/pc_kits.py")" = "$PCK_FROM" ] || { say "!! [2/7] $FIN/pc_kits.py is $(m5 "$FIN/pc_kits.py"), not the S451 file $PCK_FROM - someone changed it since the build; nothing installed"; exit 1; }
say "[2/7] pc_kits.py at its S451 pin"

"$SPY" -m py_compile built/pc_kits.py walk_s460.py 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
clean
say "[3/7] compiles"

WOUT="$( cd /tmp && timeout 300 "$SPY" -B "$KDIR/walk_s460.py" --new "$KDIR/built/pc_kits.py" --old "$FIN/pc_kits.py" --kits "$KITS" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^   FAILED|^WALK_S460' | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S460 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -30 | cut -c1-400; clean; exit 1; }
say "[4/7] walk green: the Reception PC's setup file is byte for byte what it was; each new button hands out its own PC's kit and nothing else; a code cannot cross to another PC's key list"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BP="$FIN/pc_kits.py.bak_S460_$(echo "$PCK_FROM" | cut -c1-8)"
\cp -p "$FIN/pc_kits.py" "$BP" && [ "$(m5 "$BP")" = "$PCK_FROM" ] || { say "!! [5/7] the backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backup: $BP"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BP" "$FIN/pc_kits.py"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   pc_kits.py $(m5 "$FIN/pc_kits.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
\cp -p built/pc_kits.py "$FIN/pc_kits.py" || restore "copy pc_kits.py"; chmod 644 "$FIN/pc_kits.py"
[ "$(m5 "$FIN/pc_kits.py")" = "$PCK_TO" ] || restore "md5 read-back of pc_kits.py"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/pcs"); case "$c2" in 302|401) ;; *) restore "/finance/pcs answered $c2 without a login";; esac
c3=$(health -X POST "$FINURL/finance/pcs/setup/medical"); case "$c3" in 302|401|403) ;; *) restore "the Medical PC's button answered $c3 without a login";; esac
D1="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D1" | grep -q 'Clinic PCs page' || restore "the kit door no longer refuses a request without a code in its own words"
D2="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D2" | grep -q '"NOT_YOU"' || restore "the Reception PC's heartbeat door no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pin · clinic-finance active · healthz 200 · /finance/pcs $c2 and the new button $c3 (the login gate) · the kit door and the heartbeat door answer as before · journal clean"

NOW="$(PC_KITS_ROOT="$KITS" "$SPY" -B -c "
import importlib.util, sys
s = importlib.util.spec_from_file_location('pck_now', sys.argv[1]); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print('; '.join('%s: %s' % (p['label'].encode('ascii', 'replace').decode(), (m.kit_info(p['id']) or {}).get('version', 'NO KIT')) for p in m.PCS if p['id'] in m.SETUPS))" "$FIN/pc_kits.py" 2>&1 | tail -1)"
say "[7/7] the buttons the page now offers -- $NOW"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/pc_kits.py"
