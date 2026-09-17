#!/bin/bash
# =============================================================================
#  install_S296_ATTENDANCE_NAMES.sh · kit S296_ATTENDANCE_NAMES (session 265, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S296_ATTENDANCE_NAMES/install_S296_ATTENDANCE_NAMES.sh
#
#  WHY. S295's attendance map: logins sandeep and vikky do not open 'Meri attendance' -- their staff rows are
#  spelled Sandip and Vikki, so neither the username nor the first-name rule finds them.
#  WHAT. Data only: staff.username on those two rows in /root/staff_register/staff_register.db. No code file,
#  no restart (the register reads the mapping on every request). Backup of the database before the write.
#  Gates: SUMS/KIT_ID -> compile -> selftest (11) -> S295 live -> dry run on the real database (any guard
#  refused = nothing written) -> write + read-back -> the attendance map must show both as yes.
#  Any red after the write: exactly these two usernames are cleared again.
# =============================================================================
set -u
KIT="S296_ATTENDANCE_NAMES"; KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; ROOT="${ROOT:-/root}"
USERS="$ROOT/portal/clinic_users.json"; RDB="$ROOT/staff_register/staff_register.db"
PAIRS=(sandeep=sandip vikky=vikki)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/6] SUMS.md5 gate failed - nothing written"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/6] KIT_ID names another kit - nothing written"; exit 1; }
echo "[1/6] kit gates green"
T="$(mktemp -d /tmp/s296_XXXXXX)"; cp -p set_usernames_s296.py attendance_map_s295.py "$T/"
"$SPY" -m py_compile "$T/set_usernames_s296.py" "$T/attendance_map_s295.py" || { echo "!! [2/6] compile failed - nothing written"; rm -rf "$T"; exit 1; }
( cd "$T" && "$SPY" -B set_usernames_s296.py --selftest 2>&1 | tail -1 | grep -q "^SELFTEST OK" ) || { echo "!! [2/6] selftest red - nothing written"; rm -rf "$T"; exit 1; }
rm -rf "$T"; echo "[2/6] compile + selftest (11 checks) green"
[ "$(m5 "$ROOT/portal/portal.py")" = "c14c2c649e0405378abcd95d8749c666" ] || { echo "!! [3/6] S295 is not live (portal.py) - nothing written"; exit 1; }
[ -f "$USERS" ] && [ -f "$RDB" ] || { echo "!! [3/6] $USERS or $RDB missing - nothing written"; exit 1; }
echo "[3/6] S295 live; login store and register database present"
DRY="$("$SPY" -B set_usernames_s296.py "$USERS" "$RDB" "${PAIRS[@]}" --dry 2>&1)"; echo "$DRY" | sed 's/^/      /'
if echo "$DRY" | grep -q "^RESULT REFUSED"; then echo "!! [4/6] a guard refused - nothing written"; exit 1; fi
if echo "$DRY" | grep -q "0 to set, 2 already"; then
  echo "-- ALREADY INSTALLED. The attendance map (read-only):"; "$SPY" -B attendance_map_s295.py "$USERS" "$RDB" 2>&1; exit 0; fi
echo "$DRY" | grep -q "^RESULT DRY" || { echo "!! [4/6] dry run did not complete - nothing written"; exit 1; }
echo "[4/6] dry run green on the real database"
undo() { "$SPY" -B set_usernames_s296.py "$USERS" "$RDB" "${PAIRS[@]}" --undo 2>&1 | sed 's/^/      /'; echo "!! restored: the two usernames cleared again"; }
OUT="$("$SPY" -B set_usernames_s296.py "$USERS" "$RDB" "${PAIRS[@]}" 2>&1)"; echo "$OUT" | sed 's/^/      /'
echo "$OUT" | grep -q "^RESULT OK" || { echo "!! [5/6] write/read-back red"; undo; exit 1; }
echo "[5/6] written and read back (backup named above)"
MAP="$("$SPY" -B attendance_map_s295.py "$USERS" "$RDB" 2>&1)"; echo "$MAP"
for l in sandeep vikky; do
  echo "$MAP" | grep -Eq "^$l +[a-z]+ +yes" || { echo "!! [6/6] the map does not show $l as yes"; undo; exit 1; }
done
echo "[6/6] sandeep and vikky now open Meri attendance"
echo "== S296_ATTENDANCE_NAMES INSTALLED =="
