#!/bin/bash
# rehearse_s731.sh -- S731's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM
# asset_register.py (63a8b15b) and sorting_desk.py (4990350b), the read-only files at their pins and the app's other top-level code
# files, a made-up database, no service (restart = true, health faked).
#   bash rehearse_s731.sh <folder with the FROM files>
# R1 DRY=1 nothing placed . R2 DONE: both files at their TO pins, two backups, the lock released . R3 ALREADY INSTALLED . R4 a FROM
# file of other bytes: REFUSED, nothing placed . R5 another build's lock: REFUSED, left in place . R6 health red after placing: both
# files back byte-identically, NOT INSTALLED . R7 a read-only file (stationery.py) of other bytes: REFUSED, nothing placed.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"
PY="${S731_PYTHON:-python3}"
R="$(mktemp -d /tmp/s731reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -14 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S731_APP_DIR="$R/app" S731_DB="$R/app/assets.db" S731_LOCK="$R/lockdir/lock" S731_HOST="$(hostname)" S731_REHEARSAL=1 S731_RESTART_CMD=true S731_SLEEP=0 \
        S731_HEALTH_TRIES=2 S731_FAKE_HEALTH=200 S731_PYTHON="$PY" "$@" bash "$R/kit/install_s731.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ [ "$(md5sum "$R/app/asset_register.py" | cut -c1-32)" = "$(pinof $1_asset_register)" ] && [ "$(md5sum "$R/app/sorting_desk.py" | cut -c1-32)" = "$(pinof $1_sorting_desk)" ]; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM; ok $? "R1 DRY=1: walked and controlled, then stops -- both files untouched"
inst; grep -q "S731_CHALLAN_READ: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.py\.bak_S731_')" = 2 ] && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, both files at their TO pins, two backups, the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S731
ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S731_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM
ok $? "R6 health red after placing: both files back byte-identically, NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/stationery.py"; inst; grep -q "REFUSED: stationery.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S731
ok $? "R7 a read-only file (stationery.py) of other bytes: REFUSED, nothing placed"
echo "REHEARSAL S731: $OK green, $BAD red"
[ "$BAD" = 0 ]
