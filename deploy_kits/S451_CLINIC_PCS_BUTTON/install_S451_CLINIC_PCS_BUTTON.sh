#!/bin/bash
# =============================================================================
# install_S451_CLINIC_PCS_BUTTON.sh -- session 290, 02-Oct-2026 -- F-684, F-685 (the first live use of S450).
#   REPLACE  /root/finance/pc_kits.py   104aca6d (S450) -> this kit's
#     F-684  the Clinic PCs button refused its own owner: S450 held the request's Origin to this server's address, and
#            behind the front server (OpenLiteSpeed, F-68) the owner's own press came back 403. Now a press is refused
#            only when the browser says it came from another site -- and every refusal says why, on the page and in
#            the trail.
#     F-685  the setup file did not ask which computer it was on. It now names the computer, stops on MEDICAL and
#            MANOJZ, asks when the name is not RECEPTIONPC; the enrol door refuses the other PCs' names too.
#   NOT TOUCHED: finance_app.py (e8dbf77e), reception_door.py, the portal, the kit files in deploy_kits/PC_KITS.
# Walked first on a scratch copy of /root/finance and finance.db, with the box as it is as the negative control.
# Restarts clinic-finance only; anything red after placing -> the S450 file is put back. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S451_CLINIC_PCS_BUTTON"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; POR="$ROOT/portal"
KITS="${KITS:-$(cd "$KDIR/.." && pwd)/PC_KITS}"
DBF="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
FROM=104aca6d44857722e7312123611a973d
APPPIN=e8dbf77e8a4dbd3dd83486ed6ebf68a5; DOOR=dfd557bcae7e2712e6d1e9a8b86d68f5
KITZIP=f6a9502b98615f13c6ac7f991e1cbc2f; PYZIP=30a7b6ab01fbaa598844f4b3d8220a68
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s451_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$WALK"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask - nothing installed"; exit 1; }
[ -f "$DBF" ] || { say "!! [1/7] $DBF is not there - nothing installed"; exit 1; }
[ "$(m5 "$KITS/reception/kit.zip")" = "$KITZIP" ] && [ "$(m5 "$KITS/_shared/pyportable_3.11.9.zip")" = "$PYZIP" ] && grep -q "^kit_md5=$KITZIP$" "$KITS/reception/KIT_INFO.txt" \
  || { say "!! [1/7] the Reception PC's kit in $KITS is not the one this kit was walked with - nothing installed"; exit 1; }
TO="$(m5 built/pc_kits.py)"
say "[1/7] kit gates green (SUMS, KIT_ID, flask, finance.db, the Reception PC's kit in the repository clone)"

if [ "$(m5 "$FIN/pc_kits.py")" = "$TO" ]; then say "-- ALREADY INSTALLED: $FIN/pc_kits.py is at the kit's pin; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
[ "$(m5 "$FIN/pc_kits.py")" = "$FROM" ] || { say "!! [2/7] $FIN/pc_kits.py is $(m5 "$FIN/pc_kits.py"), not the S450 file $FROM - nothing installed"; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$APPPIN" ] || { say "!! [2/7] $FIN/finance_app.py is $(m5 "$FIN/finance_app.py"), not the S450 pin $APPPIN - someone changed it since the build; nothing installed"; exit 1; }
[ "$(m5 "$FIN/reception_door.py")" = "$DOOR" ] || { say "!! [2/7] $FIN/reception_door.py is not the S449 file - nothing installed"; exit 1; }
say "[2/7] pc_kits.py is the S450 file; finance_app.py (S450) and reception_door.py (S449) at their pins"

"$SPY" -m py_compile built/pc_kits.py walk_s451.py 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] compiles"

for side in new old; do
  mkdir -p "$WALK/$side/finance_ui" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null; cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/" 2>/dev/null
  [ -d "$FIN/spine" ] && { mkdir -p "$WALK/$side/spine"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; }
  rm -f "$WALK/$side/reception_heartbeat.json" "$WALK/$side/pc_kit_codes.json"
done
mkdir -p "$WALK/sso"
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$WALK/sso/"; done   # never the live secret, never the user store
\cp -p built/pc_kits.py "$WALK/new/pc_kits.py"
[ "$(m5 "$WALK/new/pc_kits.py")" = "$TO" ] && [ "$(m5 "$WALK/old/pc_kits.py")" = "$FROM" ] || { say "!! [4/7] the scratch copies are not what they should be - nothing installed"; clean; exit 1; }
copydb "$DBF" "$WALK/scratch_fin.db" || { say "!! [4/7] no scratch copy of finance.db - nothing installed"; clean; exit 1; }
WOUT="$( cd "$WALK" && timeout 1200 "$SPY" -B "$KDIR/walk_s451.py" --new "$WALK/new" --old "$WALK/old" --sso "$WALK/sso" --db "$WALK/scratch_fin.db" --kits "$KITS" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^   FAILED|^WALK_S451|^-- old: WALK_S451|probe exit' | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S451 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -30 | cut -c1-400; clean; exit 1; }
say "[4/7] walk green on scratch copies (the press in a real browser's shapes, the setup file, the enrol door, the chain a setup file runs); the box as it is shows the defect, as it must"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BAK="$FIN/pc_kits.py.bak_S451_$(echo "$FROM" | cut -c1-8)"
\cp -p "$FIN/pc_kits.py" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [5/7] backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backup: $BAK"
restore() {
  say "!! RED after placing ($1) - restoring the S450 file"
  \cp -p "$BAK" "$FIN/pc_kits.py"; systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   $FIN/pc_kits.py $(m5 "$FIN/pc_kits.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
\cp -p built/pc_kits.py "$FIN/pc_kits.py" || restore "copy pc_kits.py"; chmod 644 "$FIN/pc_kits.py"
[ "$(m5 "$FIN/pc_kits.py")" = "$TO" ] || restore "md5 read-back of pc_kits.py"
[ "$(m5 "$FIN/finance_app.py")" = "$APPPIN" ] || restore "finance_app.py changed under the install"
say "[6/7] placed; pc_kits.py read back = the kit's pin $TO"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/pcs"); case "$c2" in 302|401) ;; *) restore "/finance/pcs answered $c2 without a login";; esac
c3=$(health -X POST "$FINURL/finance/pcs/setup/reception"); case "$c3" in 302|401) ;; *) restore "the button answered $c3 without a login";; esac
D1="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D1" | grep -q 'Clinic PCs page' || restore "the kit door did not answer a request with no code with its own refusal: $(echo "$D1" | cut -c1-160)"
D2="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D2" | grep -q '"NOT_YOU"' || restore "the reception door (S449) no longer answers"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[7/7] clinic-finance active · healthz 200 · /finance/pcs $c2 and the button $c3 without a login (the login gate) · the kit door refuses a request with no code · the reception door still answers · journal clean"
clean
say "all green -- $KIT: DONE. The button on the Clinic PCs page is pressed next from Claude's own browser - nothing for you to do."
md5sum "$FIN/pc_kits.py" "$FIN/finance_app.py"
