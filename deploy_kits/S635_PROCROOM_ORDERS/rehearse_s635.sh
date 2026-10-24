#!/bin/bash
# rehearse_s635.sh -- S635's installer on a MADE-UP root (never the live box): a copy of the kit, a folder holding the FROM
# sorting_desk.py and procroom.py and the read-only files at their pins (and the app's other top-level code files), a made-up
# database, no service (restart = true, health faked).
#   bash rehearse_s635.sh <folder with the FROM files>
# R1 DRY=1 nothing placed . R2 DONE: both files at their TO pins, two backups and the database's, the floor set, the lock released .
# R3 ALREADY INSTALLED . R4 a FROM file of other bytes: REFUSED, nothing placed . R5 another build's lock: REFUSED, left in place .
# R6 health red after placing: both files back byte-identically, NOT INSTALLED . R7 a read-only file of other bytes: REFUSED, nothing
# placed . R8 the data step run again by hand: the floor unchanged.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?the folder with the FROM files}"
PY="${S635_PYTHON:-python3}"
R="$(mktemp -d /tmp/s635reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
OK=0; BAD=0
ok(){ if [ "$1" = 0 ]; then OK=$((OK+1)); echo "GREEN $2"; else BAD=$((BAD+1)); echo "RED   $2"; tail -12 "$R/out.txt"; fi; }
cp -r "$HERE" "$R/kit"
mk(){ rm -rf "$R/app" "$R/lockdir"; mkdir -p "$R/app" "$R/lockdir"; for f in "$SRC"/*.py "$SRC"/*.js "$SRC"/*.json; do [ -f "$f" ] && cp -p "$f" "$R/app/"; done
      "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE made_up(x)'); c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)'); c.commit()" "$R/app/assets.db"; }
inst(){ env S635_APP_DIR="$R/app" S635_DB="$R/app/assets.db" S635_LOCK="$R/lockdir/lock" S635_HOST="$(hostname)" S635_REHEARSAL=1 S635_RESTART_CMD=true S635_SLEEP=0 \
        S635_HEALTH_TRIES=2 S635_FAKE_HEALTH=200 S635_PYTHON="$PY" "$@" bash "$R/kit/install_s635.sh" > "$R/out.txt" 2>&1; }
pinof(){ tr -d ' \r\n' < "$R/kit/PIN_$1.txt"; }
at(){ [ "$(md5sum "$R/app/sorting_desk.py" | cut -c1-32)" = "$(pinof $1_sorting_desk)" ] && [ "$(md5sum "$R/app/procroom.py" | cut -c1-32)" = "$(pinof $1_procroom)" ]; }
floor(){ "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); r=c.execute(\"SELECT value FROM settings WHERE key='procroom.orders_from'\").fetchone(); print(r[0] if r else '')" "$R/app/assets.db" 2>/dev/null; }

mk; inst DRY=1; grep -q "DRY RUN" "$R/out.txt" && at FROM && [ -z "$(floor)" ]; ok $? "R1 DRY=1: rebuilt, walked and controlled, then stops -- both files untouched, no floor"
inst; F1="$(floor)"; grep -q "S635_PROCROOM_ORDERS: DONE" "$R/out.txt" && at TO && [ "$(ls "$R/app" | grep -c '\.py\.bak_S635_')" = 2 ] \
  && [ "$(ls "$R/app" | grep -c 'assets\.db\.bak_S635_')" = 1 ] && [ -n "$F1" ] && grep -q "floor: procroom.orders_from set to" "$R/out.txt" && [ ! -e "$R/lockdir/lock" ]
ok $? "R2 the install: DONE, both files at their TO pins, two backups and the database's, the floor set ($F1), the lock released"
inst; grep -q "ALREADY INSTALLED" "$R/out.txt" && at TO; ok $? "R3 a second run: ALREADY INSTALLED"
"$PY" -B "$R/app/procroom.py" --floor "$R/app/assets.db" > "$R/out.txt" 2>&1; grep -q "already set" "$R/out.txt" && [ "$(floor)" = "$F1" ]
ok $? "R8 the data step run again by hand: the floor unchanged"
mk; echo "# other bytes" >> "$R/app/sorting_desk.py"; inst; grep -q "REFUSED: sorting_desk.py is" "$R/out.txt" && ! ls "$R/app" | grep -q bak_S635
ok $? "R4 a FROM file of other bytes: REFUSED, nothing placed"
mk; mkdir -p "$R/lockdir/lock"; echo other > "$R/lockdir/lock/owner"; inst; grep -q "another build holds the lock" "$R/out.txt" && [ -f "$R/lockdir/lock/owner" ] && at FROM
ok $? "R5 another build's lock: REFUSED, its lock left in place"
mk; inst S635_FAKE_HEALTH=500; grep -q "NOT INSTALLED (restored)" "$R/out.txt" && at FROM
ok $? "R6 health red after placing: both files back byte-identically, NOT INSTALLED"
mk; echo "# other bytes" >> "$R/app/claude_reader.py"; inst; grep -q "REFUSED: claude_reader.py is" "$R/out.txt" && at FROM && ! ls "$R/app" | grep -q bak_S635
ok $? "R7 a read-only file of other bytes: REFUSED, nothing placed"
echo "REHEARSAL S635: $OK green, $BAD red"
[ "$BAD" = 0 ]
