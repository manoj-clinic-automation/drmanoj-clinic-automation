#!/bin/bash
# rehearse_s656.sh -- S656's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM
# procroom.py (S648's) and the read-only files at their pins (and the app's other top-level code files), a made-up database, no
# service (restart = true, health faked).
#   bash rehearse_s656.sh <folder with the FROM files>
# R1 DRY=1 nothing placed . R2 DONE: procroom.py at its TO pin, its backup and the database's, the lock released . R3 ALREADY
# INSTALLED . R4 a FROM file of other bytes: REFUSED, nothing placed . R5 another build's lock: REFUSED, left in place . R6 health red
# after placing: the file back byte-identically, NOT INSTALLED . R7 a read-only file (the desk) of other bytes: REFUSED, nothing placed.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"
PY="${S656_PYTHON:-python3}"
R="$(mktemp -d /tmp/s656reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -12 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S656_APP_DIR="$R/app" S656_DB="$R/app/assets.db" S656_LOCK="$R/lockdir/lock" S656_HOST="$(hostname)" S656_REHEARSAL=1 S656_RESTART_CMD=true S656_SLEEP=0 \
        S656_HEALTH_TRIES=2 S656_FAKE_HEALTH=200 S656_PYTHON="$PY" "$@" bash "$R/kit/install_s656.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ [ "$(md5sum "$R/app/procroom.py" | cut -c1-32)" = "$(pinof $1_procroom)" ]; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM; ok $? "R1 DRY=1: walked and controlled, then stops -- the file untouched"
inst; grep -q "S656_PROCROOM_SMALL_POINTS: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.py\.bak_S656_')" = 1 ] \
  && [ "$(ls "$R/app" | grep -c 'assets\.db\.bak_S656_')" = 1 ] && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, procroom.py at its TO pin, its backup and the database's, the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"
mk; echo "# other bytes" >> "$R/app/procroom.py"; inst; grep -q "REFUSED: procroom.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S656
ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S656_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM
ok $? "R6 health red after placing: the file back byte-identically, NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S656
ok $? "R7 a read-only file (the desk) of other bytes: REFUSED, nothing placed"
echo "REHEARSAL S656: $OK green, $BAD red"
[ "$BAD" = 0 ]
