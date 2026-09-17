#!/bin/bash
# =============================================================================
#  install_S298_PRAVESH_EXIT.sh · kit S298_PRAVESH_EXIT (session 265, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S298_PRAVESH_EXIT/install_S298_PRAVESH_EXIT.sh
#
#  THE OWNER, 17-Sep: "parvesh quit, i tried your flow for exit a leaver but was confused midway."
#  FOUND: six steps ticked on 16-Sep, but step 7 is not a tick -- staff_master.csv still had Pravesh
#  (code 17) active, the attendance register still had him active, code 17 was never retired.
#   A  joiner_app.py 3e213e4d -> PREDICTED: an EXIT's step 7 now says "staff master and attendance register
#      updated -- the person no longer appears" and that Claude does it (the JOIN wording is unchanged).
#   B  exit_s298.py does step 7 for Pravesh: staff_master.csv active N (one byte), register last working
#      31-Aug + inactive, code 17 retired, step 7 ticked, record COMPLETE. Gate: August LOCKED.
#  Gates: SUMS/KIT_ID -> pin -> compile -> exit selftest (12) -> walk over a scratch copy of finance.db (6,
#  old file must fail) -> dry run on the real stores -> place + restart + health -> the real run.
#  Any red after placing: joiner_app.py restored, data changes undone, clinic-finance restarted.
# =============================================================================
set -u
KIT="S298_PRAVESH_EXIT"; KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
FROM_JA="3e213e4dfd4171eb4cf3bbcd0538025b"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s298_walk_$STAMP"
EXARGS=(--finance-db "$FIN/finance.db" --register-db "$ROOT/staff_register/staff_register.db" --staff-master "$ROOT/staff_master.csv" --punches "$ROOT/punches.csv" --state "$FIN/exit_s298_state.json")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/7] SUMS.md5 gate failed - nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/7] KIT_ID names another kit - nothing changed"; exit 1; }
echo "[1/7] kit gates green"
TO_JA="$(m5 joiner_app.py)"
if [ "$(m5 "$FIN/joiner_app.py")" = "$TO_JA" ] && "$SPY" -B exit_s298.py "${EXARGS[@]}" --dry 2>&1 | grep -q "^RESULT ALREADY"; then
  echo "-- ALREADY INSTALLED: joiner_app.py $TO_JA, and Pravesh's exit is complete."; exit 0; fi
[ "$(m5 "$FIN/joiner_app.py")" = "$FROM_JA" ] || [ "$(m5 "$FIN/joiner_app.py")" = "$TO_JA" ] || { echo "!! [2/7] $FIN/joiner_app.py is $(m5 "$FIN/joiner_app.py"), expected $FROM_JA - nothing changed"; exit 1; }
echo "[2/7] live pin exact"
"$SPY" -m py_compile joiner_app.py exit_s298.py walk_s298.py || { echo "!! [3/7] compile failed - nothing changed"; exit 1; }
T="$WALK/t"; mkdir -p "$T" && cp -p exit_s298.py "$T/"
( cd "$T" && "$SPY" -B exit_s298.py --selftest --schema "$FIN/joiner_schema.sql" 2>&1 | tail -1 | grep -q "^SELFTEST OK" ) || { echo "!! [3/7] exit selftest red - nothing changed"; rm -rf "$WALK"; exit 1; }
echo "[3/7] compile + exit selftest (12 checks) green"
mkdir -p "$WALK/new" "$WALK/old" && cp -p joiner_app.py "$FIN/joiner_schema.sql" "$WALK/new/" && cp -p "$FIN/joiner_app.py" "$FIN/joiner_schema.sql" "$WALK/old/"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d)" "$FIN/finance.db" "$WALK/walk.db" || { echo "!! [4/7] scratch copy failed - nothing changed"; rm -rf "$WALK"; exit 1; }
W1="$("$SPY" -B walk_s298.py "$WALK/new" "$WALK/walk.db" 2>&1 | tail -1)"; W0="$("$SPY" -B walk_s298.py "$WALK/old" "$WALK/walk.db" 2>&1 | grep -c "WALK FAIL")"
[ "${W1#WALK OK}" != "$W1" ] && [ "$W0" = 1 ] || { echo "!! [4/7] walk red ($W1 / old-file control $W0) - nothing changed"; rm -rf "$WALK"; exit 1; }
DRY="$("$SPY" -B exit_s298.py "${EXARGS[@]}" --dry 2>&1)"; echo "$DRY" | sed 's/^/      /'
echo "$DRY" | grep -q "^RESULT DRY\|^RESULT ALREADY" || { echo "!! [4/7] dry run refused - nothing changed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"; echo "[4/7] walk 6 checks on a copy of finance.db (old file red) · dry run green on the real stores"
BAK="$FIN/joiner_app.py.bak_S298_$(m5 "$FIN/joiner_app.py" | cut -c1-8)"
restore() { echo "!! RED - restoring"; [ -f "$FIN/exit_s298_state.json" ] && "$SPY" -B exit_s298.py "${EXARGS[@]}" --undo 2>&1 | sed 's/^/      /'
  [ -f "$BAK" ] && \cp -p "$BAK" "$FIN/joiner_app.py"; systemctl restart clinic-finance || true; sleep 3
  echo "!! restored: joiner_app.py $(m5 "$FIN/joiner_app.py"), clinic-finance $(systemctl is-active clinic-finance)"; exit 1; }
[ -f "$BAK" ] || \cp -p "$FIN/joiner_app.py" "$BAK"
\cp -p joiner_app.py "$FIN/joiner_app.py" && [ "$(m5 "$FIN/joiner_app.py")" = "$TO_JA" ] || restore
systemctl restart clinic-finance || restore; sleep 4; systemctl is-active --quiet clinic-finance || restore
c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz); echo "      health : finance $c1"; [ "$c1" = 200 ] || restore
echo "[5/7] joiner_app.py placed ($TO_JA, backup $BAK), clinic-finance restarted, health 200"
OUT="$("$SPY" -B exit_s298.py "${EXARGS[@]}" 2>&1)"; echo "$OUT" | sed 's/^/      /'
echo "$OUT" | grep -q "^RESULT OK\|^RESULT ALREADY" || restore
echo "[6/7] Pravesh's exit done and read back (backups named above)"
"$SPY" -B exit_s298.py "${EXARGS[@]}" --dry 2>&1 | grep -q "^RESULT ALREADY" || restore
echo "[7/7] re-check: all three stores say he has left"
echo "== S298_PRAVESH_EXIT INSTALLED =="
