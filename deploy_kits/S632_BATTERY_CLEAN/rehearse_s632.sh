#!/bin/bash
# rehearse_s632.sh -- S632's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM batteries.py
# and the read-only files, a made-up database, no service (restart = true, health faked).
#   bash rehearse_s632.sh <folder with the FROM batteries.py and asset_register.py, sorting_desk.py, clinic_papers.py, asset_machine.py,
#                          stationery.py, xray_costs.py at their pins (and the app's other top-level code files)>
# R1 DRY=1 nothing placed . R2 DONE: batteries.py at its TO pin, the backup beside it, the lock released . R3 ALREADY INSTALLED .
# R4 a FROM file of other bytes: REFUSED, nothing placed . R5 another build's lock: REFUSED, left in place . R6 health red after placing:
# the file back byte-identically, NOT INSTALLED . R7 a read-only file of other bytes: REFUSED, nothing placed.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"
PY="${S632_PYTHON:-python3}"
R="$(mktemp -d /tmp/s632reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -8 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S632_APP_DIR="$R/app" S632_DB="$R/app/assets.db" S632_LOCK="$R/lockdir/lock" S632_HOST="$(hostname)" S632_REHEARSAL=1 S632_RESTART_CMD=true S632_SLEEP=0 \
        S632_HEALTH_TRIES=2 S632_FAKE_HEALTH=200 S632_PYTHON="$PY" "$@" bash "$R/kit/install_s632.sh" > "$R/out.txt" 2>&1; }
at(){ [ "$(md5sum "$R/app/batteries.py" | cut -c1-32)" = "$(tr -d ' \r\n' < "$R/kit/PIN_$1_batteries.txt")" ]; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM; ok $? "R1 DRY=1: rebuilt, walked and controlled, then stops -- the file untouched"
inst; grep -q "S632_BATTERY_CLEAN: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.bak_S632_')" = 1 ] && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, batteries.py at its TO pin, one backup, the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/app/batteries.py"; inst; grep -q "REFUSED: batteries.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S632; ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S632_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM; ok $? "R6 health red after placing: the file back byte-identically, NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S632
ok $? "R7 a read-only file of other bytes: REFUSED, nothing placed"
echo "REHEARSAL S632: $OK green, $BAD red"
[ "$BAD" = 0 ]
