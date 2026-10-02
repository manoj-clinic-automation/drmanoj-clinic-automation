#!/bin/bash
# =============================================================================
# install_S450_CLINIC_PCS_TILE.sh -- session 290, 02-Oct-2026 -- D660.
# THE OWNER, 02-Oct-2026: the PC kits on the server, "a tile on my portal for all these kits ... by a very simple click,
# run and install the agent in that PC" -- and, on the mock: "looks good to me. Go ahead with it."
#   NEW   /root/finance/pc_kits.py          /finance/pcs (the owner only), the button's setup file with a one-time code,
#                                           the two doors the setup file uses (fetch the kit; enrol the PC's new key)
#   EDIT  /root/finance/finance_app.py      022a9b0e (S449): the two api paths, the guarded mount, the mounts row = 27
#   EDIT  /root/portal/portal.py            ba61e35a (S444): the tile "Clinic PCs", in Admin, granted by name to manoj
#   EDIT  /root/portal/tile_grants.json     392e6d89 (v31) : "Clinic PCs" in manoj's extra; version 32
# The kit the page serves is in this repository clone: deploy_kits/PC_KITS/reception/kit.zip + _shared/ (checked below).
# Walked first on scratch copies of /root/finance, /root/portal (never portal_config.py) and finance.db. Restarts
# clinic-finance and clinic-portal; anything red after placing -> every file restored. DRY=1 places nothing.
# =============================================================================
set -u
KIT="S450_CLINIC_PCS_TILE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; POR="$ROOT/portal"
KITS="${KITS:-$(cd "$KDIR/.." && pwd)/PC_KITS}"
DBF="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"; PORURL="${PORURL:-http://127.0.0.1:8099}"
declare -A FROM=( [finance_app.py]=022a9b0e3b0b22e748a1283d53c2c201 [portal.py]=ba61e35a9a2a2722d19304d791e255ca [tile_grants.json]=392e6d89b09bcc7127cc541224771206 )
declare -A TO=( [finance_app.py]=e8dbf77e8a4dbd3dd83486ed6ebf68a5 [portal.py]=1a9fb99dfab46621a91c3fa041e37b50 [tile_grants.json]=f9441311cd413bc4c12e9d4e23feb791 )
declare -A DIR=( [finance_app.py]="$FIN" [portal.py]="$POR" [tile_grants.json]="$POR" )
declare -A WHICH=( [finance_app.py]=finance [portal.py]=portal [tile_grants.json]=grants )
ORDER=(finance_app.py tile_grants.json portal.py)
DOOR=dfd557bcae7e2712e6d1e9a8b86d68f5
KITZIP=f6a9502b98615f13c6ac7f991e1cbc2f; PYZIP=30a7b6ab01fbaa598844f4b3d8220a68
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s450_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$WALK"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/8] $SPY lacks flask - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/8] the venv python lacks flask - nothing installed"; exit 1; }
[ -f "$DBF" ] || { say "!! [1/8] $DBF is not there - nothing installed"; exit 1; }
[ "$(m5 "$KITS/reception/kit.zip")" = "$KITZIP" ] && [ "$(m5 "$KITS/_shared/pyportable_3.11.9.zip")" = "$PYZIP" ] && grep -q "^kit_md5=$KITZIP$" "$KITS/reception/KIT_INFO.txt" \
  || { say "!! [1/8] the Reception PC's kit in $KITS is not the one this kit was walked with - nothing installed"; exit 1; }
PK_TO="$(m5 built/pc_kits.py)"
say "[1/8] kit gates green (SUMS, KIT_ID, flask on both pythons, finance.db, the Reception PC's kit in the repository clone)"

ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || ALL=0; done; [ "$(m5 "$FIN/pc_kits.py")" = "$PK_TO" ] || ALL=0
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: all four files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null), clinic-portal $(systemctl is-active clinic-portal 2>/dev/null)"; exit 0; fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "${DIR[$f]}/$f")" = "${FROM[$f]}" ] || { say "!! [2/8] ${DIR[$f]}/$f is $(m5 "${DIR[$f]}/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the build; nothing installed"; exit 1; }
done
[ "$(m5 "$FIN/reception_door.py")" = "$DOOR" ] || { say "!! [2/8] $FIN/reception_door.py is not the S449 file - install S449 first; nothing installed"; exit 1; }
[ ! -e "$FIN/pc_kits.py" ] || { say "!! [2/8] $FIN/pc_kits.py already exists - nothing installed"; exit 1; }
say "[2/8] finance_app.py (S449), portal.py and tile_grants.json at their FROM pins; reception_door.py is the S449 file; pc_kits.py not there yet"

( "$SPY" -m py_compile built/pc_kits.py apply_s450.py walk_s450.py && "$VPY" -m py_compile apply_s450.py ) 2>/dev/null || { say "!! [3/8] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/8] compiles on both pythons"

for side in new old; do
  mkdir -p "$WALK/$side/finance_ui" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null; cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/" 2>/dev/null
  [ -d "$FIN/spine" ] && { mkdir -p "$WALK/$side/spine"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; }
  rm -f "$WALK/$side/reception_heartbeat.json" "$WALK/$side/pc_kit_codes.json"
done
for side in por_new por_old; do
  mkdir -p "$WALK/$side"
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$WALK/$side/"; done   # never the live secret, never the user store
  cp -p "$POR/tile_grants.json" "$WALK/$side/"
done
cp -p built/pc_kits.py "$WALK/new/" && "$SPY" -B apply_s450.py finance "$WALK/new/finance_app.py" >/dev/null \
  && "$SPY" -B apply_s450.py portal "$WALK/por_new/portal.py" >/dev/null && "$SPY" -B apply_s450.py grants "$WALK/por_new/tile_grants.json" >/dev/null
[ "$(m5 "$WALK/new/finance_app.py")" = "${TO[finance_app.py]}" ] && [ "$(m5 "$WALK/por_new/portal.py")" = "${TO[portal.py]}" ] && [ "$(m5 "$WALK/por_new/tile_grants.json")" = "${TO[tile_grants.json]}" ] \
  || { say "!! [4/8] a patched copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile "$WALK/new/finance_app.py" 2>/dev/null && "$VPY" -m py_compile "$WALK/por_new/portal.py" 2>/dev/null \
  && "$SPY" -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); assert d['version']==32 and 'Clinic PCs' in d['users']['manoj']['extra']" "$WALK/por_new/tile_grants.json" \
  || { say "!! [4/8] a patched copy does not compile or parse - nothing installed"; clean; exit 1; }
copydb "$DBF" "$WALK/scratch_fin.db" || { say "!! [4/8] no scratch copy of finance.db - nothing installed"; clean; exit 1; }
WOUT="$( cd "$WALK" && FINANCE_SSO_DIR="$WALK/por_old" timeout 1200 "$SPY" -B "$KDIR/walk_s450.py" --new "$WALK/new" --old "$WALK/old" --por-new "$WALK/por_new" --por-old "$WALK/por_old" \
         --db "$WALK/scratch_fin.db" --kits "$KITS" --vpy "$VPY" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^   FAILED|^WALK_S450|probe exit' | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S450 GREEN" || { say "!! [4/8] walk red - nothing installed"; echo "$WOUT" | tail -30 | cut -c1-400; clean; exit 1; }
say "[4/8] walk green on scratch copies (the finance app, the portal, the chain a setup file runs); the box as it is has no page and no tile, as it must"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="${DIR[$f]}/$f.bak_S450_$(echo "${FROM[$f]}" | cut -c1-8)"
  \cp -p "${DIR[$f]}/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [5/8] backup of $f failed - nothing placed"; clean; exit 1; }
done
say "[5/8] backups: .bak_S450_<from8> beside each of the three files"
restore() {
  say "!! RED after placing ($1) - restoring"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DIR[$f]}/$f"; done; rm -f "$FIN/pc_kits.py"
  systemctl restart clinic-finance 2>/dev/null || true; systemctl restart clinic-portal 2>/dev/null || true; sleep 7
  for f in "${ORDER[@]}"; do say "   ${DIR[$f]}/$f $(m5 "${DIR[$f]}/$f")"; done
  say "   pc_kits.py removed · finance healthz $(health "$FINURL/finance/healthz") · portal health $(health "$PORURL/portal/health")"
  clean; exit 1
}
\cp -p built/pc_kits.py "$FIN/pc_kits.py" || restore "copy pc_kits.py"; chmod 644 "$FIN/pc_kits.py"
for f in "${ORDER[@]}"; do "$SPY" -B apply_s450.py "${WHICH[$f]}" "${DIR[$f]}/$f" | sed 's/^/      /'; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
[ "$(m5 "$FIN/pc_kits.py")" = "$PK_TO" ] || restore "md5 read-back of pc_kits.py"
say "[6/8] placed; all four md5s read back = the kit's pins"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
systemctl restart clinic-portal || restore "restart clinic-portal"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
systemctl is-active --quiet clinic-portal || restore "clinic-portal not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/pcs"); case "$c2" in 302|401) ;; *) restore "/finance/pcs answered $c2 without a login";; esac
D1="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D1" | grep -q 'Clinic PCs page' || restore "the kit door did not answer a request with no code with its own refusal: $(echo "$D1" | cut -c1-160)"
D2="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D2" | grep -q '"NOT_YOU"' || restore "the reception door (S449) no longer answers"
p1=$(health "$PORURL/portal/health"); p2=$(health "$PORURL/portal/login")
[ "$p1" = 200 ] || restore "portal /portal/health $p1"
for s in clinic-finance clinic-portal; do
  journalctl -u "$s" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "$s: a module NOT mounted"
  JR="$(journalctl -u "$s" --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
  [ "${JR:-0}" = 0 ] || restore "$s journal: $JR error line(s)"
done
say "[7/8] both services active · finance healthz 200 · /finance/pcs $c2 (the login gate) · the kit door refuses a request with no code · the reception door still answers · portal health $p1, login $p2 · journals clean"

sleep 20
HBAGE="$("$SPY" -c "
import json,sys,time
try:
    r=json.load(open(sys.argv[1])); print('%d minute(s) ago, agent %s' % ((time.time()-r['received_ts'])/60, r['beat'].get('agent_version')))
except Exception as ex:
    print('not read (%s)' % ex)" "$FIN/reception_heartbeat.json")"
say "[8/8] the reception PC's last direct report: $HBAGE"
clean
say "all green -- $KIT: DONE. On your portal, under Admin: the tile 'Clinic PCs'."
md5sum "$FIN/finance_app.py" "$FIN/pc_kits.py" "$POR/portal.py" "$POR/tile_grants.json"
