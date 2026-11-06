#!/bin/bash
# rehearse_s735.sh -- S735's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM
# stationery.py (3a22c6bb, S674's); asset_register.py (5f44f65e, S731) and sorting_desk.py (52e959da, S732) read only, the read-only files at their pins and the app's other top-level code
# files, a made-up database, no service (restart = true, health faked).
#   bash rehearse_s735.sh <folder with the FROM files>
# R1 DRY=1 nothing placed . R2 DONE: the file at its TO pin, its backup, the lock released . R3 ALREADY INSTALLED . R4 a FROM
# file of other bytes: REFUSED, nothing placed . R5 another build's lock: REFUSED, left in place . R6 health red after placing: the
# file back byte-identically, NOT INSTALLED . R7 a read-only file (sorting_desk.py) of other bytes: REFUSED, nothing placed.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"
PY="${S735_PYTHON:-python3}"
R="$(mktemp -d /tmp/s735reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -14 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S735_APP_DIR="$R/app" S735_DB="$R/app/assets.db" S735_LOCK="$R/lockdir/lock" S735_HOST="$(hostname)" S735_REHEARSAL=1 S735_RESTART_CMD=true S735_SLEEP=0 \
        S735_HEALTH_TRIES=2 S735_FAKE_HEALTH=200 S735_PYTHON="$PY" "$@" bash "$R/kit/install_s735.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ [ "$(md5sum "$R/app/stationery.py" | cut -c1-32)" = "$(pinof $1_stationery)" ]; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM; ok $? "R1 DRY=1: walked and controlled, then stops -- the file untouched"
inst; grep -q "S735_STMT_LAST_MONTH: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.py\.bak_S735_')" = 1 ] && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, the file at its TO pin, its backup, the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/app/stationery.py"; inst; grep -q "REFUSED: stationery.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S735
ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S735_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM
ok $? "R6 health red after placing: the file back byte-identically, NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S735
ok $? "R7 a read-only file (sorting_desk.py) of other bytes: REFUSED, nothing placed"
echo "REHEARSAL S735: $OK green, $BAD red"
[ "$BAD" = 0 ]
